<div align="center">

# 🛰️ OrbitMap 轨道可视化工具

交互式航天器轨道可视化:**3D 地球轨道动画 + 2D 墨卡托地面轨迹**,支持 TLE 加载、实时晨昏线(昼夜分界)与卫星覆盖范围(footprint)渲染。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey)

</div>

---

## ✨ 功能特性

| 模块 | 说明 |
|---|---|
| 🪐 3D 轨道动画 | Three.js 渲染 ECI 惯性系轨道管、卫星标记、地面投影点、赤道环、坐标轴、星空;播放/暂停、进度拖拽、速度调节 |
| 🗺️ 2D 地面轨迹 | Leaflet 墨卡托投影多圈地面轨迹 + 卫星实时标记;离线地图瓦片(Esri 卫星图 / OSM) |
| 🌗 晨昏线黑夜区域 | 由太阳位置计算晨昏大圆,黑夜半球半透明填充,随地球旋转实时更新;极昼/极夜与跨日界线场景正确 |
| 📡 覆盖范围 footprint | 按轨道高度与最小仰角计算球冠:2D 填充 + 3D 地表圆环与卫星锥体;**极点、跨日界线场景由 d3-geo 球面裁剪正确处理** |
| 🛰️ TLE 支持 | 快速加载(ISS / 天宫 / Hubble / NOAA 19 / GPS)或粘贴两行 TLE 自动解析,平近点角随时间推进;支持自定义历元与模拟开始时间 |
| 🛸 星座跟踪 | 一键加载并跟踪 GPS / 北斗 / 风云气象 / 星链 / 铱星 NEXT / 伽利略 / 格洛纳斯 / OneWeb 等星座,在线实时 TLE 优先、本地预设兜底;支持采样数量、卫星下拉选择、单星联动查看、星下点轨迹与覆盖热力图 |
| 🧮 轨道计算 | 开普勒方程求解、3-1-3 欧拉旋转 ECI 变换、含地球自转的地面轨迹、近地点/远地点/周期等轨道根数 |
| 📴 离线可用 | Leaflet / Three.js / 地球贴图 / d3 全部本地化于 `static/vendor/`,瓦片缺失时自动使用占位图;**仅在线拉取 TLE(单星/星座)需要联网** |

## 🚀 快速开始

```bash
pip install -r requirements.txt
python app.py          # 启动后自动打开 http://127.0.0.1:5000
```

Windows 下可直接双击 `start.bat`。无需联网即可运行:所有前端库均已本地化,瓦片缺失时自动显示离线占位图。

### 地图瓦片(可选,需联网一次)

```bash
python scripts/download_esri_tiles.py   # Esri 卫星图 zoom 0-5(约 1365 张)
python scripts/download_tiles.py        # OSM 地图 zoom 0-3
```

瓦片目录(`static/tiles/`)体积大,已在 `.gitignore` 中排除,不入库。断网或未下载时页面会自动使用 `static/placeholder.png` 占位图;也可运行 `python scripts/generate_tiles.py` 生成网格占位瓦片。

### 星座跟踪

侧边栏顶部可切换 **单星 Satellite / 星座 Constellation** 两种模式(二选一,星座数据缓存保留,切换不重新联网)。**Constellation 星座跟踪** 区域:

1. 选择星座组(GPS / 北斗 / 风云气象 / 星链 / 铱星 NEXT / 伽利略 / 格洛纳斯 / OneWeb)与采样数量;
2. 点击 **Load 加载星座**:优先从 CELESTRAK 拉取实时 TLE(需联网);拉取失败或断网时自动回退到本地预设快照(`static/data/constellation_presets.json`),结果面板会标明数据源与更新时间;
3. 3D 视图显示各卫星轨道环与实时位置,2D 地图显示卫星标记与星下点轨迹;
4. 通过 **选择卫星下拉框** 或点击 2D 地图标记切换高亮跟踪卫星,并查看其轨道参数;
5. 点击 **单星查看** 可将选中卫星一键载入单星模式(表单、轨道与结果面板自动更新,含卫星名称);
6. 开启 **Coverage 覆盖范围**:2D 地图以热力图显示全部卫星的覆盖区域,无需选中卫星,颜色随重叠卫星数量变化(1 蓝 / 2 青 / 3 绿 / 4 橙 / 5+ 红);单星模式下仍保留 3D 锥体/圆环与 2D 精确轮廓;
7. 模拟开始时间(单星/星座共用)修改后,星座会按新时刻自动重算;
8. 点击 **Clear 清除** 返回单星模式。

大星座(如星链)默认按采样数量均匀抽样,避免浏览器卡顿;采样数量可在 10-200 之间调节。

本地预设快照可用以下脚本随时刷新(需联网一次):

```bash
python scripts/fetch_constellation_presets.py
```

## 🔌 API

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/compute` | POST | 输入 `perigee`/`apogee`/`inclination`/`raan`/`arg_perigee`/`num_orbits`/`mean_anomaly`(km、度),返回轨道根数、3D 轨道坐标、地面轨迹分段(JSON) |
| `/api/compute-constellation` | POST | 批量计算星座轨道:输入 `satellites` 数组(每项含 `name` 与轨道参数),返回每颗星的轨道环、多圈动画坐标与轨道根数 |
| `/api/fetch-tle` | GET | 按 NORAD ID(`?catnr=25544`)或星座组(`?group=gps-ops`)从 CELESTRAK 代理获取 TLE,解决跨域问题 |

## 📁 项目结构

```
app.py                      Flask 后端(API + 页面)
orbit_calc.py               轨道计算核心(开普勒方程、ECI/ECEF 变换、地面轨迹)
templates/index.html        单页前端(Three.js 3D + Leaflet 2D + d3-geo SVG 覆盖层)
static/
  vendor/
    leaflet/                Leaflet JS/CSS/图标(本地化)
    three/                  Three.js 模块与 OrbitControls(本地化)
  textures/               地球贴图(本地化)
  d3-array.min.js         d3-array(本地化)
  d3-geo.min.js           d3-geo(本地化)
  data/                   星座本地预设快照(constellation_presets.json)
  tiles/                    离线地图瓦片(esri / osm)
  placeholder.png           离线地图占位瓦片(缺失瓦片自动回退)
scripts/                    工具脚本
  download_esri_tiles.py    Esri 卫星瓦片下载
  download_tiles.py         OSM 瓦片下载
  generate_tiles.py         占位瓦片/回退瓦片生成
  fetch_constellation_presets.py  抓取 CELESTRAK 星座 TLE 生成本地预设
start.bat                   Windows 启动脚本
```

## 🛠️ 技术说明

- **2D 覆盖层渲染**:晨昏线黑夜区域与覆盖球冠以球面多边形(GeoJSON)交给 `d3.geoPath` 渲染——d3-geo 内置 antimeridian 与极点球面裁剪,跨日界线/极地场景自动拆分为正确的子路径;投影同步层使用 `L.CRS.EPSG3857.latLngToPoint`(浮点、无取整)与 Leaflet 像素坐标精确对齐
- **物理模型**:二体问题、圆/椭圆轨道;`MU = 398600.4418 km³/s²`、`R_EARTH = 6378.137 km`、`OMEGA_E = 7.2921159e-5 rad/s`;纬度采用地心纬度(非大地纬度),存在轻微近似
- **离线策略**:页面不引用任何 CDN;Leaflet、Three.js、OrbitControls、地球贴图与 d3 全部位于 `static/vendor/`;地图瓦片缺失时 `errorTileUrl` 回退到 `static/placeholder.png`。只有实时 TLE 拉取(`/api/fetch-tle`)依赖外部网络,失败时星座自动使用本地预设快照
- **星座实现**:前端解析多星 TLE 并按模拟开始时间传播平近点角,后端批量计算(ECI 动画数组),动画按各星周期模长插值,统一由地球自转(GST)驱动 2D/3D 同步
- **开发提示**:Flask 以 `debug=False` 运行时会缓存模板,修改 `templates/index.html` 后需重启 `python app.py`

## 📄 许可证

[MIT License](LICENSE) © 2026 Helium

地图瓦片版权归各数据提供方(Esri / OpenStreetMap),仅供学习研究使用。
