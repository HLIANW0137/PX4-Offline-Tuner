PX4 Offline Tuner - Release Package

启动方式：
1. 打开 `PX4OfflineTuner` 文件夹
2. 双击 `PX4OfflineTuner.exe`
3. 如果浏览器没有自动打开，也可以双击 `Start_PX4OfflineTuner.bat`

当前发布版支持：
- CSV 和 PX4 ULog 日志导入
- 单日志分析
- 多日志联合辨识
- 频域分析、系统辨识、PID 推荐、仿真评分
- PX4 参数导出
- Markdown / JSON 报告导出

运行期输出路径：
- 分析输出：%USERPROFILE%\PX4OfflineTuner\outputs
- 应用日志：%USERPROFILE%\PX4OfflineTuner\logs\application.log

建议：
- 大日志建议把重采样频率控制在 80Hz 到 150Hz
- 如果分析失败，优先查看 application.log
- 如果浏览器没有弹出，可手动打开程序显示的 localhost 地址
