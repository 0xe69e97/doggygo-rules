# doggygo-rules

国内分流规则集（sing-box 源格式 JSON），给狗狗加速 / Doggygo 客户端用的远程规则地址。

规则数据来自 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) 的 `sing` 分支，
由 GitHub Actions 每天自动重建。

## 远程地址

远程规则地址（仓库：`0xe69e97/doggygo-rules`）。

### 推荐：jsDelivr CDN（国内可直连，有缓存加速）

```
https://cdn.jsdelivr.net/gh/0xe69e97/doggygo-rules@main/rules/direct-cn.json
https://cdn.jsdelivr.net/gh/0xe69e97/doggygo-rules@main/rules/ads.json
https://cdn.jsdelivr.net/gh/0xe69e97/doggygo-rules@main/rules/proxy-cn.json
https://cdn.jsdelivr.net/gh/0xe69e97/doggygo-rules@main/rules/geoip-cn.json
```

备用镜像（jsDelivr 抽风时换这个）：

```
https://fastly.jsdelivr.net/gh/0xe69e97/doggygo-rules@main/rules/direct-cn.json
```

### GitHub 原始地址（国内常被墙，仅作最后备用）

```
https://raw.githubusercontent.com/0xe69e97/doggygo-rules/main/rules/direct-cn.json
```

> **注意缓存**：jsDelivr 对 `@main` 这类分支引用有约 12 小时缓存。
> 想要"改了立刻生效"，用时间戳 tag 代替 `@main`（工作流每天会打一个 `vYYYY.MM.DD` 的 tag）：
> `https://cdn.jsdelivr.net/gh/0xe69e97/doggygo-rules@v2026.09.23/rules/direct-cn.json`

## 客户端怎么配

### 在狗狗加速里怎么填

客户端「自定义规则」页的两个关键规则（截图上写着的原话）：
**「规则勾选生效，列表从上到下按顺序匹配」**。

所以每条规则有 **两个** 必须设对的属性 —— **动作** 和 **勾选状态**，光填地址没用。

1. 进「规则 → 自定义规则 → 远程规则」，逐条添加下面的地址
2. 每条**设置正确的动作**（客户端会显示成 `REJECT` / `DIRECT` 之类的徽标）
3. 每条**勾选**左边的复选框，否则不生效
4. 顺序按下面排，**从上往下匹配，不能反**

| 顺序 | 规则地址 | 动作 | 勾选 |
|---|---|---|---|
| 1 | `rules/ads.json` | 拦截 / REJECT | ✅ |
| 2 | `rules/direct-cn.json` | 直连 / DIRECT | ✅ |
| 3 | `rules/geoip-cn.json` | 直连 / DIRECT | ✅ |
| 4 | 兜底（客户端内置） | 代理 / PROXY | — |

> ⚠️ **两个最常见的坑**：
> 1. 把直连规则的动作设成了 `REJECT` —— 那不是"直连"，是"**拉黑**"，
>    会把这些域名全部阻断，症状比走代理还糟。
> 2. 添加了但**没勾选** —— 完全等同没配。
>
> 踩过一次：`direct-cn.json` 填进去后报「远程规则仅支持 JSON 或 SRS 文件」。
> 真因不是格式，是**版本号**：客户端要求 rule-set `version >= 3`，
> 而 MetaCubeX 的 `sing` 分支发布的是 `version 2`。本仓库所有文件已升到 v3。

**第 3 条别漏。** 它是按 **IP 段** 匹配的，专门兜住那些不走域名、直接用
`IP:端口` 连接的流量（手游对战/实时语音服务器、P2P、部分 App 的私有协议）。
少了它，这类连接会一路掉到兜底 → 走境外代理 → 实时语音直接不可用。

`proxy-cn.json` 通常**不需要** —— 有了兜底规则，剩下的流量已经全走代理了。
只有当客户端**没有兜底/最终规则选项**时，才把它加上当兜底。

### 为什么需要按 IP 匹配的规则（geoip-cn.json）

手游的实时对战和语音服务器**通常由信令服务器下发 `IP:端口`**，客户端拿到 IP 后
直接连，全程没有域名。域名规则（无论多全）都抓不到这种连接，于是全部落到兜底走代理。

实测例子：《口袋狼人杀》（`com.c2vl.kgamebox`，上海假面科技）。它的官网域名
`langrensha.net`、`caniculab.com` **本来就在直连清单里**，但游戏内语音依然不可用 ——
因为语音走的是阿里云杭州的裸 IP（`118.178.168.192` / `121.40.11.144`），域名规则覆盖不到。

`geoip-cn.json` 含 9741 条国内 IP 段，覆盖上述全部地址。

### 为什么 direct-cn.json 有 1.6 MB

上游的 `geolocation-cn` 清单**缺淘宝、微博、支付宝、阿里巴巴、阿里 CDN、新浪、小红书**，
中文大站主要靠 `cn`（11 万条）覆盖，所以必须合并两者。
JSON 解析实测约 5 ms，体积换来的是这些站点不走代理 —— 不要为了省体积换精简版。

## 内置的自定义直连域名

`direct-cn.json` 里额外写入了以下域名（同时存在于 `domain` 精确匹配和 `domain_suffix` 后缀匹配）：

- `molin.myds.me`
- `smalin.myds.me`

这两个是 Synology DDNS 域名，指向国内公网 IP。上游清单不含 `myds.me`，
不手写规则的话 NAS 请求会走代理 → 从境外回连家宽 → 连不上。

改这个列表：编辑 `scripts/build.py` 里的 `EXTRA_DIRECT_HOSTS`，然后手动跑一次
`python scripts/build.py`（或等第二天的自动任务）。

> 配套的 **DNS 规则**也要加：这两个域名强制走国内 DNS（`223.5.5.5`），
> 否则会被代理 DNS 解析。示例见 `rules/singbox-config-example.json`。

## 本地重建

```bash
python scripts/build.py           # 重新生成 rules/*.json
python scripts/build.py --check   # 只检查是否有变化，有变化则 exit 1
```

脚本只用标准库，不需要装依赖。

## 许可

规则数据来自 MetaCubeX/meta-rules-dat（GPL-3.0）及上游 v2fly/domain-list-community（CC-BY-SA-4.0）。
本仓库仅做格式转换、合并与去重，未修改任何规则内容。
