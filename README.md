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

按这个顺序配，**从上往下匹配，顺序不能反**：

| 顺序 | 规则地址 | 动作 |
|---|---|---|
| 1 | `rules/ads.json` | 拦截 / REJECT |
| 2 | `rules/direct-cn.json` | 直连 / DIRECT |
| 3 | 兜底（final） | 代理 / PROXY |

`proxy-cn.json` 通常**不需要** —— 有了兜底规则，剩下的流量已经全走代理了。
只有当客户端**没有兜底/最终规则选项**时，才把它加上当兜底。

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
