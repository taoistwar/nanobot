---
name: weather
description: Get current weather and forecasts (no API key required).
homepage: https://wttr.in/:help
metadata: {"nanobot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather
天气

Two free services, no API keys needed.
两个免费服务，不需要 API key。

## wttr.in (primary)
wttr.in（主要）

Quick one-liner:
快速单行命令：
```bash
curl -s "wttr.in/London?format=3"
# Output: London: ⛅️ +8°C
```

Compact format:
紧凑格式：
```bash
curl -s "wttr.in/London?format=%l:+%c+%t+%h+%w"
# Output: London: ⛅️ +8°C 71% ↙5km/h
```

Full forecast:
完整预报：
```bash
curl -s "wttr.in/London?T"
```

Format codes: `%c` condition · `%t` temp · `%h` humidity · `%w` wind · `%l` location · `%m` moon
格式代码：`%c` 天气状况 · `%t` 温度 · `%h` 湿度 · `%w` 风 · `%l` 位置 · `%m` 月相

Tips:
提示：
- URL-encode spaces: `wttr.in/New+York`
- 对空格进行 URL 编码：`wttr.in/New+York`
- Airport codes: `wttr.in/JFK`
- 机场代码：`wttr.in/JFK`
- Units: `?m` (metric) `?u` (USCS)
- 单位：`?m`（公制）`?u`（USCS）
- Today only: `?1` · Current only: `?0`
- 仅今天：`?1` · 仅当前：`?0`
- PNG: `curl -s "wttr.in/Berlin.png" -o /tmp/weather.png`
- PNG：`curl -s "wttr.in/Berlin.png" -o /tmp/weather.png`

## Open-Meteo (fallback, JSON)
Open-Meteo（备用，JSON）

Free, no key, good for programmatic use:
免费，无需 key，适合程序化使用：
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true"
```

Find coordinates for a city, then query. Returns JSON with temp, windspeed, weathercode.
先查找城市坐标，然后查询。返回包含温度、风速和天气代码的 JSON。

Docs: https://open-meteo.com/en/docs
文档：https://open-meteo.com/en/docs
