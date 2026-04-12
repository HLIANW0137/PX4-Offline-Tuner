# PX4 Offline Tuner

`PX4 Offline Tuner` 是一个面向 PX4 飞行日志的离线自动调参工具。  
它的目标是在没有真实飞控或暂时不方便实飞的阶段，基于 `ULog` 或标准化 `CSV` 日志，完成：

- 日志解析与清洗
- 频域分析
- 系统辨识
- PID 参数推荐
- 离线仿真评估
- 报告与参数导出

当前项目已经包含源码版和 Windows 发布版，适合直接演示、继续开发、或整理后上传 GitHub。

## 核心能力

- 支持 `PX4 ULog` 与标准化 `CSV` 输入
- 支持单日志分析和多日志联合辨识
- 支持 `roll / pitch / yaw` 速率环分析
- 自动完成重采样、低通滤波、误差构造与质量评分
- 结合 PX4 控制链相关话题做日志映射：
  `vehicle_angular_velocity`、`vehicle_rates_setpoint`、`actuator_controls_0 / actuator_motors / actuator_servos`、`vehicle_attitude`、`vehicle_attitude_setpoint`、`battery_status`
- 基于 FOPDT 近似模型做系统辨识
- 提供 `conservative / balanced / aggressive` 三档 PID 推荐
- 基于闭环仿真输出性能评分、超调、上升时间、稳定性结论
- 支持 Web 可视化界面、CLI 运行、Markdown/JSON/PX4 参数导出

## 适用范围

当前版本主要适用于：

- PX4 多旋翼速率环离线分析
- 参数初值推荐
- 多份公开日志对比分析
- 无实机情况下的控制链算法验证

当前版本不做：

- 直接写入真实飞控参数
- 实时在线调参
- 完整替代实飞验证

## 输入格式

### 1. ULog

推荐直接使用 PX4 导出的 `.ulg` 日志。

当前会优先尝试映射以下主题：

- `vehicle_angular_velocity`
- `vehicle_rates_setpoint`
- `actuator_controls_0`
- `actuator_motors`
- `actuator_servos`
- `vehicle_attitude`
- `vehicle_attitude_setpoint`
- `battery_status`

### 2. CSV

CSV 至少应包含以下列：

- `timestamp_s`
- `axis`
- `rate_setpoint`
- `rate`
- `control_output`

可选列：

- `attitude_setpoint`
- `attitude`
- `battery_voltage`

其中 `axis` 取值应为：

- `roll`
- `pitch`
- `yaw`

## 快速开始

### 1. 安装源码环境

```bash
pip install -e .
```

### 2. 单日志命令行运行

```bash
px4-tuner run --input sample_data/demo_log.csv --output outputs/demo
```

### 3. 多日志联合分析

```bash
px4-tuner run --input sample_data/demo_log.csv sample_data/another_log.csv --output outputs/multi_demo
```

### 4. 启动可视化界面

```bash
px4-tuner ui
```

### 5. 直接运行 Streamlit

```bash
streamlit run src/px4_offline_tuner/webapp.py
```

## Windows 发布版

当前正式发布目录：

`release/PX4OfflineTuner/`

可直接运行：

- `release/PX4OfflineTuner/PX4OfflineTuner.exe`
- `release/PX4OfflineTuner/Start_PX4OfflineTuner.bat`

如果需要重新打包：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

运行期输出目录：

- 分析结果：`~/PX4OfflineTuner/outputs`
- 应用日志：`~/PX4OfflineTuner/logs/application.log`

## 界面说明

图形界面主要包含以下区域：

- `Overview`：整体分析结论、各轴质量评分、推荐档位
- `Axis Analysis`：单轴跟踪图、频域图、控制输出图、仿真结果
- `Exports`：PX4 参数导出、Markdown 报告、JSON 报告
- `Data Preview`：预处理后的数据预览
- `Run Details`：输入日志、输出目录、生成文件说明

如果日志较大，建议将重采样频率控制在 `80Hz ~ 150Hz`，可以明显减少页面卡顿。

## 算法流程

项目当前主流程如下：

1. 读取 ULog 或 CSV
2. 对每个轴构造统一的速率环数据
3. 重采样、低通滤波、误差计算、质量评分
4. 做频域分析并估计延迟和带宽
5. 进行单日志或多日志联合 FOPDT 系统辨识
6. 基于辨识模型生成三档 PID 推荐
7. 通过闭环仿真计算性能评分并排序
8. 输出图表、报告和参数导出文件

## 项目结构

```text
release/                    当前正式发布版
sample_data/                示例日志
scripts/                    构建脚本
src/px4_offline_tuner/      核心源码
tests/                      自动化测试
README.md                   项目说明
RELEASE_README.txt          发布版简要说明
pyproject.toml              Python 项目配置
```

核心源码模块说明：

```text
src/px4_offline_tuner/
  app_logging.py            运行日志
  cli.py                    命令行入口
  desktop.py                打包版桌面启动入口
  frequency.py              频域分析
  identification.py         系统辨识
  io_utils.py               原子写文件工具
  log_loader.py             ULog / CSV 解析
  models.py                 数据模型
  persistence.py            报告与数据回读
  pipeline.py               主分析流水线
  presentation.py           表格与导出展示层
  preprocessing.py          数据预处理
  reporting.py              报告写出
  runtime_paths.py          运行路径管理
  selection.py              推荐排序
  simulation.py             闭环仿真
  streamlit_runner.py       打包态 Streamlit 启动桥接
  tuning.py                 PID 推荐生成
  webapp.py                 Web 界面
```

## 测试

运行测试：

```bash
pytest
```

当前测试覆盖了：

- 主分析流水线
- 多日志联合分析
- 报告持久化回读
- 参数导出
- 展示层数据构造

## 上传 GitHub 建议

当前环境里没有可用的 `gh` 命令，所以这里不能直接替你发布到 GitHub。  
但项目已经整理成适合直接上传的状态，你可以这样操作：

1. 在 GitHub 新建一个仓库
2. 将当前 `PX4` 目录整体上传
3. 或者本地执行：

```bash
git init
git add .
git commit -m "Initial release of PX4 Offline Tuner"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

你的 GitHub 主页是：[HLIANW0137](https://github.com/HLIANW0137)

## 当前状态

当前项目已经具备：

- 可运行源码
- 可运行发布版
- 更详细的项目说明
- 更干净的目录结构

后续最自然的增强方向：

- 更细的 PX4 控制分层整定
- 滤波参数建议
- SITL / Gazebo 回放验证
- 更完整的 ULog 机型兼容策略
