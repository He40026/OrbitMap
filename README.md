# OrbitMap 轨道可视化工具

交互式航天器轨道可视化:3D 地球轨道动画 + 2D 墨卡托地面轨迹,支持 TLE 加载、实时晨昏线(昼夜分界)与卫星覆盖范围(footprint)渲染。

## 功能特性

- **3D 轨道动画**(Three.js):ECI 惯性系轨道管、卫星标记、地面投影点、赤道环、坐标轴、星空背景;支持播放/暂停、进度拖拽、速度调节
- **2D 地面轨迹**(Leaflet):墨卡托投影多圈地面轨迹、卫星实时位置标记;离线地图瓦片(Esri 卫星图 / OSM)
- **晨昏线黑夜区域**:基于太阳位置计算晨昏大圆,黑夜半球以半透明区域填充并实时随地球旋转更新;极昼/极夜、跨日界线场景均正确
- **覆盖范围(footprint)**:根据轨道高度与最小仰角计算球冠,2D 填充 + 3D 地表圆环与卫星锥体;**极点、跨日界线场景由 d3-geo 球面裁剪正确处理**(此前无法填充的场景现已支持)
- **TLE 支持**:快速加载(ISS / 天宫 / Hubble / NOAA 19 / GPS)或粘贴两行 TLE 自动解析,平近点角随时间推进;也可指定轨道历元 / 模拟开始时间
- **轨道计算**:开普勒方程求解、3-1-3 欧拉旋转 ECI 变换、含地球自转的地面轨迹、近地点/远地点/周期等轨道根数输出
- **离线可用**:地图瓦片本地化(scripts/download_esri_tiles.py),前端依赖 d3-geo / d3-array 亦本地化于 `static/vendor/`

## 快速开始

```bash
pip install -r requirements.txt
python app.py          # 启动后自动打开 http://127.0.0.1:5000
```

Windows 下也可直接双击 `start.bat`(自动检查瓦片,缺失时提示下载或生成占位图)。

首次运行建议执行瓦片下载(需联网,仅一次):

```bash
python scripts/download_esri_tiles.py   # Esri 卫星图 zoom 0-5(约 1365 张,需访问 arcgisonline)
python scripts/download_tiles.py        # OSM 地图 zoom 0-3
```

断网或下载失败时可生成占位瓦片: `python scripts/generate_tiles.py`

## API

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/compute` | POST | 输入 `perigee`/`apogee`/`inclination`/`raan`/`arg_perigee`/`num_orbits`/`mean_anomaly`(km、度),返回轨道根数、3D 轨道坐标、地面轨迹分段(JSON) |
| `/api/fetch-tle` | GET | 按 NORAD ID 从 CELESTRAK 代理获取 TLE(`?catnr=25544`),解决跨域问题 |

## 项目结构

```
app.py                      Flask 后端(API + 页面)
orbit_calc.py               轨道计算核心(开普勒方程、ECI/ECEF 变换、地面轨迹)
templates/index.html        单页前端(Three.js 3D + Leaflet 2D + d3-geo SVG 覆盖层)
static/vendor/              d3-array / d3-geo(本地化依赖)
static/tiles/               离线地图瓦片(esri / osm)
scripts/                    工具脚本
  download_esri_tiles.py    Esri 卫星瓦片下载
  download_tiles.py         OSM 瓦片下载
  generate_tiles.py         占位瓦片生成
start.bat                   Windows 启动脚本
```

## 技术说明

- **2D 覆盖层渲染**:晨昏线黑夜区域与覆盖球冠以球面多边形(GeoJSON)交给 `d3.geoPath` 渲染——d3-geo 内置 antimeridian 与极点球面裁剪,跨日界线/极地场景自动拆分为正确的子路径;投影同步层用 `L.CRS.EPSG3857.latLngToPoint`(浮点、无取整)与 Leaflet 像素坐标精确对齐
- **物理模型**:二体问题、圆/椭圆轨道;`MU = 398600.4418 km³/s²`、`R_EARTH = 6378.137 km`、`OMEGA_E = 7.2921159e-5 rad/s`;纬度采用地心纬度(非大地纬度),存在轻微近似
- **开发提示**:Flask 以 `debug=False` 运行时会缓存模板,修改 `templates/index.html` 后需重启 `python app.py`

## 许可

教学/个人用途。地图瓦片版权归各数据提供方(Esri / OpenStreetMap)。
