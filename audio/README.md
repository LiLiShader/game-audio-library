# 游戏音频音效资源库

面向游戏开发的音频音效资源库，分两部分，均按同一套分类体系（01~11）整理：

1. **项目提取**：从三个 Cocos Creator 休闲游戏项目中提取，共 **115 个 MP3 文件**（约 30 MB）；
2. **网络公共音效库**：从 OpenGameArt.org 与 Kenney 批量采集的 **22 个 CC0 音效包，共 1867 个音频文件**（约 300 MB），覆盖 UI、玩法、障碍、奖励等游戏通用类型，不限休闲三消品类。

## 资源来源

| 文件夹 | 项目说明 | 引擎 | 音效数量 | 大小 |
|---|---|---|---:|---:|
| [Blossom](./Blossom/) | 花卉主题牌块三消（内部名 tile-flower），含花园养成、相册、拼图等收集玩法 | Cocos Creator 2.4.12 | 67 | 见清单 |
| [mahjong-match](./mahjong-match/) | 麻将主题三消消除游戏 | Cocos Creator 2.4.x | 17 | 见清单 |
| [tile-vertical](./tile-vertical/) | 竖版牌块三消 + 房间装扮玩法 | Cocos Creator 2.4.11 | 31 | 见清单 |
| [网络公共音效库](./网络公共音效库/) | OpenGameArt.org + Kenney 采集的 22 个 CC0 音效包（全品类通用，可商用） | 格式：WAV/OGG/MP3 | 1867 | 见清单 |

## 目录结构

```
音频资源库/
├── README.md            ← 本文件
├── Blossom/
│   ├── 音频清单.md       ← 该项目全部音效的明细（含大小/时长/用途）
│   ├── 01_BGM_背景音乐/
│   ├── 02_UI_界面交互/
│   ├── 03_Gameplay_核心玩法/
│   ├── 04_Booster_道具技能/
│   ├── 05_Obstacle_障碍机关/
│   ├── 06_Reward_奖励收获/
│   ├── 07_Collection_收集图鉴/
│   ├── 08_Result_关卡结果/
│   ├── 09_Shop_商店消费/
│   └── 11_Voice_人声语音/
├── mahjong-match/
│   ├── 音频清单.md
│   └── （同上分类体系，仅保留该项目用到的分类）
├── tile-vertical/
│   ├── 音频清单.md
│   └── （同上分类体系，另含 10_Life_体力生命）
└── 网络公共音效库/
    ├── README.md        ← 22 个来源包的来源/许可/统计
    ├── 音频清单.md       ← 全部 1867 个文件明细
    └── 02~10 等分类/
        └── <音效包>/    ← 每包含 SOURCE.txt（来源+许可）
```

## 分类体系

| 分类编号 | 含义 |
|---|---|
| 01_BGM_背景音乐 | 场景/对局循环背景乐 |
| 02_UI_界面交互 | 按钮、弹窗开闭、翻页、选择等界面音 |
| 03_Gameplay_核心玩法 | 牌块点击、消除匹配、收集等核心玩法动作音 |
| 04_Booster_道具技能 | 洗牌、撤销、锤子、冰冻等道具/技能音 |
| 05_Obstacle_障碍机关 | 冰块、锁链、草丛等障碍生成/解除音 |
| 06_Reward_奖励收获 | 奖励、礼物、宝箱、金币相关音 |
| 07_Collection_收集图鉴 | 相册、拼图等收集系统音 |
| 08_Result_关卡结果 | 过关/失败/结算音 |
| 09_Shop_商店消费 | 商店、购买音 |
| 10_Life_体力生命 | 体力增减音 |
| 11_Voice_人声语音 | 人声语音 |

## 跨项目重复说明（MD5 完全一致的文件）

三个项目之间存在复用素材，取用时按需挑选即可：

| 音效内容 | 出现位置 |
|---|---|
| 通用按钮点击 ui_button | Blossom = mahjong-match（tile-vertical 版本不同） |
| 弹窗打开 ui_open | Blossom = mahjong-match（Blossom 的 setting_en 即此文件） |
| 获得奖励 reward_get / get_reward | 三个项目完全相同 |
| 宝箱开启 box_open | Blossom = mahjong-match |
| 奖励漂浮 reward_float | Blossom = mahjong-match |
| 通用收集 collect = quest_click | Blossom 内部复用 + mahjong-match 同款 |
| 冰块碎裂 level_ice = obstacle_ice_crack | Blossom = mahjong-match |
| 解锁 level_unlock = obstacle_lockbox_unlock | Blossom = mahjong-match |
| 过关胜利 level_victory | Blossom 的 passLevel_en 即此文件（mahjong-match 版本不同） |
| 撤销 prop_pause2 = booster_undo | Blossom = tile-vertical |
| 收集品弹出 collection_pop = coin_fly | Blossom = tile-vertical |
| Blossom 内部：quest_coin = gift_goup、gift_levelup = bonuslevel_appear | 同一文件两处使用 |

## 使用说明

- 项目提取音频为 MP3，公共音效另含 WAV、OGG，可按目标引擎与平台支持情况导入。
- 文件名保留了项目原始命名（个别保留源项目拼写，如 `folwer_up`、`bosster_auto_match`），便于回溯源码。
- 命名规律：`ui_*` 界面、`booster_*` 道具、`level_*` / `obstacle_*` / `tile_element_*` 障碍、`reward_*` 奖励、`album_*` / `puzzle_*` 收集。
- 各文件的大小、时长、用途明细见各项目文件夹内的 `音频清单.md`。
