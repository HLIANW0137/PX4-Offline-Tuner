from __future__ import annotations

import json
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from px4_offline_tuner.app_logging import get_logger
from px4_offline_tuner.frequency import compute_power_spectrum
from px4_offline_tuner.persistence import load_run_report
from px4_offline_tuner.pipeline import PX4OfflineTuner
from px4_offline_tuner.presentation import (
    available_sample_logs,
    best_recommendation,
    build_overview_table,
    build_px4_param_text,
    build_ranked_recommendation_table,
    build_recommendation_table,
    load_report_artifacts,
)
from px4_offline_tuner.runtime_paths import default_output_root, log_root, project_root


PROJECT_ROOT = project_root()
OUTPUT_ROOT = default_output_root()
LOGGER = get_logger("px4_offline_tuner.webapp")


st.set_page_config(page_title="PX4 Offline Tuner", page_icon="PX4", layout="wide")


def _downsample_frame(frame: pd.DataFrame, max_points: int = 2500) -> pd.DataFrame:
    if len(frame) <= max_points:
        return frame
    step = max(1, len(frame) // max_points)
    return frame.iloc[::step].reset_index(drop=True)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .hero {
            padding: 1.25rem 1.5rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 60%, #38bdf8 100%);
            color: white;
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
        }
        .hero p {
            margin: 0.5rem 0 0 0;
            opacity: 0.95;
            font-size: 1rem;
        }
        .soft-card {
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            background: rgba(15, 23, 42, 0.03);
        }
        .axis-chip {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(59, 130, 246, 0.12);
            color: #2563eb;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>PX4 Offline Tuner</h1>
            <p>把公开 PX4 日志转成可解释的频域诊断、系统辨识、PID 推荐、仿真验证和参数导出结果。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_tracking_figure(axis_report) -> go.Figure:
    frame = _downsample_frame(axis_report.dataset.data, max_points=2500)
    figure = go.Figure()
    figure.add_scatter(x=frame["timestamp_s"], y=frame["rate_setpoint"], mode="lines", name="Setpoint")
    figure.add_scatter(x=frame["timestamp_s"], y=frame["rate"], mode="lines", name="Measured rate")
    figure.add_scatter(
        x=frame["timestamp_s"],
        y=frame["tracking_error"],
        mode="lines",
        name="Tracking error",
        line={"dash": "dot"},
    )
    figure.update_layout(
        title=f"{axis_report.axis.upper()} Tracking",
        xaxis_title="Time (s)",
        yaxis_title="Rate",
        height=360,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def _build_control_figure(axis_report) -> go.Figure:
    frame = _downsample_frame(axis_report.dataset.data, max_points=2500)
    figure = go.Figure()
    figure.add_scatter(x=frame["timestamp_s"], y=frame["control_output"], mode="lines", name="Control output")
    figure.update_layout(
        title=f"{axis_report.axis.upper()} Control Output",
        xaxis_title="Time (s)",
        yaxis_title="Normalized output",
        height=320,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def _build_frequency_figure(axis_report) -> go.Figure:
    frame = _downsample_frame(axis_report.dataset.data, max_points=4096)
    sample_rate = axis_report.dataset.sample_rate_hz
    freqs_rate, pxx_rate = compute_power_spectrum(frame["rate"].to_numpy(dtype=float), sample_rate)
    freqs_error, pxx_error = compute_power_spectrum(frame["tracking_error"].to_numpy(dtype=float), sample_rate)

    figure = go.Figure()
    figure.add_scatter(x=freqs_rate, y=pxx_rate, mode="lines", name="Rate PSD")
    figure.add_scatter(x=freqs_error, y=pxx_error, mode="lines", name="Error PSD")
    figure.update_layout(
        title=f"{axis_report.axis.upper()} Frequency Response Snapshot",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Power spectral density",
        height=320,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def _build_simulation_figure(axis_report) -> go.Figure:
    table = build_recommendation_table(axis_report)
    figure = go.Figure()
    figure.add_bar(name="Rise time (s)", x=table["preset"], y=table["rise_time_s"])
    figure.add_bar(name="Settling time (s)", x=table["preset"], y=table["settling_time_s"])
    figure.add_bar(name="Overshoot (%)", x=table["preset"], y=table["overshoot_pct"])
    figure.update_layout(
        title=f"{axis_report.axis.upper()} Simulation Comparison",
        barmode="group",
        height=340,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def _render_welcome() -> None:
    left, right = st.columns([1.15, 1.0], gap="large")
    with left:
        st.subheader("软件能力")
        st.markdown(
            """
            - 支持 `CSV` 和 `ULog` 日志输入
            - 自动完成速率环数据清洗、频域分析和简化系统辨识
            - 提供 `conservative / balanced / aggressive` 三档 PID 推荐
            - 自动生成仿真验证、Markdown 报告、JSON 报告和 PX4 参数导出文本
            """
        )
    with right:
        st.subheader("建议使用流程")
        st.markdown(
            """
            1. 选择样例日志或上传真实日志  
            2. 设置输出目录和重采样频率  
            3. 运行分析并查看总览结论  
            4. 对比各轴推荐参数和仿真结果  
            5. 导出 PX4 参数文本用于后续仿真或实机测试
            """
        )


def _run_analysis(source_paths: list[Path], output_name: str, target_rate_hz: float) -> None:
    output_dir = OUTPUT_ROOT / output_name
    tuner = PX4OfflineTuner(target_rate_hz=target_rate_hz)
    LOGGER.info("Starting analysis for %s logs into %s", len(source_paths), output_dir)
    if len(source_paths) == 1:
        report = tuner.run(source_paths[0], output_dir)
    else:
        report = tuner.run_many(source_paths, output_dir)
    st.session_state["latest_report_dir"] = str(output_dir)
    st.session_state["latest_output_dir"] = output_dir
    st.session_state["latest_source_list"] = [str(path) for path in source_paths]
    LOGGER.info("Analysis completed for %s logs into %s", len(source_paths), output_dir)
    return report


def _render_overview(report) -> None:
    overview_table = build_overview_table(report)
    avg_quality = overview_table["quality_score"].mean()
    avg_fit = overview_table["fit_score"].mean()
    stable_ratio = float(overview_table["stable"].mean()) if not overview_table.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("已分析轴数量", len(report.axis_reports))
    c2.metric("平均质量评分", f"{avg_quality:.2f}")
    c3.metric("平均模型拟合", f"{avg_fit:.2f}")
    c4.metric("仿真稳定比例", f"{stable_ratio * 100:.0f}%")

    st.subheader("整体结论")
    for line in report.summary:
        st.write(f"- {line}")

    st.subheader("轴向总览")
    st.dataframe(overview_table, use_container_width=True, hide_index=True)

    card_columns = st.columns(len(report.axis_reports))
    for idx, axis_report in enumerate(report.axis_reports):
        best = best_recommendation(axis_report)
        sim = axis_report.simulations[best.preset]
        with card_columns[idx]:
            st.markdown(f"<div class='soft-card'><div class='axis-chip'>{axis_report.axis.upper()}</div>", unsafe_allow_html=True)
            st.metric("推荐档位", best.preset)
            st.metric("质量 / 拟合", f"{axis_report.dataset.quality_score:.2f} / {axis_report.model.fit_score:.2f}")
            st.metric("超调 / 上升", f"{sim.overshoot_pct:.1f}% / {sim.rise_time_s:.2f}s")
            st.markdown("</div>", unsafe_allow_html=True)


def _render_axis_report(axis_report) -> None:
    best = best_recommendation(axis_report)
    best_sim = axis_report.simulations[best.preset]

    st.markdown(f"<div class='axis-chip'>{axis_report.axis.upper()} Axis</div>", unsafe_allow_html=True)
    top1, top2, top3, top4, top5 = st.columns(5)
    top1.metric("质量评分", f"{axis_report.dataset.quality_score:.2f}")
    top2.metric("带宽估计", f"{axis_report.frequency.bandwidth_estimate_hz:.2f} Hz")
    top3.metric("模型拟合", f"{axis_report.model.fit_score:.2f}")
    top4.metric("时延", f"{axis_report.model.dead_time_s:.3f} s")
    top5.metric("最佳档位", best.preset, delta=f"score {best_sim.performance_score:.1f}")

    chart_left, chart_right = st.columns(2, gap="large")
    chart_left.plotly_chart(_build_tracking_figure(axis_report), use_container_width=True)
    chart_right.plotly_chart(_build_control_figure(axis_report), use_container_width=True)

    chart_left, chart_right = st.columns(2, gap="large")
    chart_left.plotly_chart(_build_frequency_figure(axis_report), use_container_width=True)
    chart_right.plotly_chart(_build_simulation_figure(axis_report), use_container_width=True)

    st.subheader("诊断说明")
    for text in axis_report.dataset.quality_notes + axis_report.frequency.diagnosis + axis_report.model.notes:
        st.write(f"- {text}")

    st.subheader("PID 推荐对比")
    recommendation_table = build_recommendation_table(axis_report)
    st.dataframe(recommendation_table, use_container_width=True, hide_index=True)

    st.subheader("推荐排序")
    st.dataframe(build_ranked_recommendation_table(axis_report), use_container_width=True, hide_index=True)

    st.subheader("推荐理由")
    for recommendation in axis_report.recommendations:
        with st.expander(f"{recommendation.preset} preset | risk={recommendation.risk}"):
            for rationale in recommendation.rationale:
                st.write(f"- {rationale}")


def _render_exports(report) -> None:
    artifacts = load_report_artifacts(report)
    preset = st.selectbox("选择要导出的参数档位", ["conservative", "balanced", "aggressive"], index=1)
    param_text = build_px4_param_text(report, preset)

    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "下载 PX4 参数",
        data=param_text,
        file_name=f"px4_params_{preset}.params",
        mime="text/plain",
        use_container_width=True,
    )
    c2.download_button(
        "下载 Markdown 报告",
        data=artifacts.get("markdown", ""),
        file_name="report.md",
        mime="text/markdown",
        use_container_width=True,
    )
    c3.download_button(
        "下载 JSON 报告",
        data=artifacts.get("json", json.dumps(report.to_dict(), indent=2)),
        file_name="report.json",
        mime="application/json",
        use_container_width=True,
    )

    st.subheader("PX4 参数预览")
    st.code(param_text, language="text")

    st.subheader("报告预览")
    preview_tab1, preview_tab2 = st.tabs(["Markdown", "JSON"])
    preview_tab1.code(artifacts.get("markdown", ""), language="markdown")
    preview_tab2.code(artifacts.get("json", json.dumps(report.to_dict(), indent=2)), language="json")


def _render_data_preview(report) -> None:
    axis_names = [item.axis for item in report.axis_reports]
    selected_axis = st.selectbox("选择轴查看原始预处理数据", axis_names)
    axis_report = next(item for item in report.axis_reports if item.axis == selected_axis)
    frame = _downsample_frame(axis_report.dataset.data.copy(), max_points=1500)
    st.dataframe(frame.round(6), use_container_width=True, height=420)


def _render_run_details(report) -> None:
    source_list = st.session_state.get("latest_source_list", [str(report.input_path)])
    st.write(f"输入数量: `{len(report.input_paths)}`")
    for source in source_list:
        st.write(f"- 输入来源: `{source}`")
    st.write(f"结果目录: `{report.output_dir}`")
    st.write(f"日志目录: `{log_root()}`")
    st.write("生成文件")
    for path in sorted(report.output_dir.rglob("*")):
        if path.is_file():
            st.write(f"- `{path.relative_to(report.output_dir.parent)}`")


_inject_styles()
_render_header()

sample_logs = available_sample_logs(PROJECT_ROOT)
default_output_name = f"streamlit_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

with st.sidebar:
    st.header("运行设置")
    source_mode = st.radio("日志来源", ["样例日志", "上传日志"], index=0)
    selected_samples: list[Path] = []
    uploaded_files = []

    if source_mode == "样例日志":
        sample_names = [path.name for path in sample_logs]
        if sample_names:
            selected_names = st.multiselect("选择一个或多个样例", sample_names, default=sample_names[:1])
            selected_samples = [path for path in sample_logs if path.name in selected_names]
        else:
            st.warning("当前没有找到样例日志。")
    else:
        uploaded_files = st.file_uploader("上传一个或多个 CSV / ULog", type=["csv", "ulg"], accept_multiple_files=True)

    target_rate_hz = st.slider("重采样频率 (Hz)", min_value=20, max_value=400, value=120, step=10)
    output_name = st.text_input("输出目录名", value=default_output_name)
    run_button = st.button("开始分析", type="primary", use_container_width=True)

    st.caption("提示：大型日志建议先用 80-150Hz 做离线分析，能明显降低界面卡顿风险。")

if run_button:
    try:
        if source_mode == "样例日志":
            if not selected_samples:
                st.warning("没有可用的样例日志。")
            else:
                with st.spinner("正在分析样例日志..."):
                    _run_analysis(selected_samples, output_name, float(target_rate_hz))
                st.success("分析完成，结果已刷新。")
        else:
            if not uploaded_files:
                st.warning("请先上传日志文件。")
            else:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_paths: list[Path] = []
                    for idx, uploaded in enumerate(uploaded_files):
                        suffix = Path(uploaded.name).suffix
                        temp_path = Path(temp_dir) / f"uploaded_{idx}{suffix}"
                        temp_path.write_bytes(uploaded.getbuffer())
                        temp_paths.append(temp_path)
                    with st.spinner("正在分析上传日志..."):
                        _run_analysis(temp_paths, output_name, float(target_rate_hz))
                st.success("分析完成，结果已刷新。")
    except Exception as exc:
        LOGGER.exception("Analysis failed")
        st.error(f"分析失败: {exc}")
        st.exception(exc)
        st.code(traceback.format_exc(), language="python")
        st.info(f"详细日志见: {log_root() / 'application.log'}")

report = None
report_dir = st.session_state.get("latest_report_dir")
if report_dir:
    try:
        report = load_run_report(report_dir)
    except Exception:
        LOGGER.exception("Failed to load persisted report from %s", report_dir)
        st.error("结果目录中的报告无法重新载入，请重新执行分析。")
        st.info(f"详细日志见: {log_root() / 'application.log'}")

if report is None:
    _render_welcome()
else:
    tabs = st.tabs(["Overview", "Axis Analysis", "Exports", "Data Preview", "Run Details"])
    with tabs[0]:
        _render_overview(report)
    with tabs[1]:
        axis_tabs = st.tabs([item.axis.upper() for item in report.axis_reports])
        for tab, axis_report in zip(axis_tabs, report.axis_reports, strict=False):
            with tab:
                _render_axis_report(axis_report)
    with tabs[2]:
        _render_exports(report)
    with tabs[3]:
        _render_data_preview(report)
    with tabs[4]:
        _render_run_details(report)
