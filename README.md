修改仅用于个人使用
# Fofa-hack (Multi-Dimensional Slicing Edition)

> 针对非付费会员优化的 FOFA 数据高效采集与多维切片查询工具。
> 
> Forked from [Cl0udG0d/Fofa-hack](https://github.com/Cl0udG0d/Fofa-hack)
> 
> 感谢原项目作者及所有贡献者们。

---

## 本次自用优化的核心：
1. **引入多维笛卡尔积细分查询**：通过对资产属性进行多层交叉组合（如：域名状态 × 国家地区 × 云厂商），将大范围检索拆解为多个精确的小范围子任务，大幅提升资产覆盖面和命中率。
2. **增强 429 容错与重试机制**：内置了智能退避与延时重试策略。当触发接口限流时，程序会自动暂停冷却并重试，确保组合任务能够全自动、稳定地跑完全程，不会半途崩溃。

---

## 🔍 多维细分查询逻辑说明

本版本支持**多层笛卡尔积组合查询**，查询顺序与层级结构如下：

1. **第 1 层：主体关键字（Base Search Key）**
   * 例如：`body="xxx"`（可自定义）。
2. **第 2 层：资产类型（Domain Status）**
   * 区分是否为独立域名：`is_domain="false"`（IP直连/非域名资产）与 `is_domain="true"`（标准域名资产）。
3. **第 3 层：国家与地区（Countries）**
   * 细分全球主流国家/地区，如：`JP`, `US`, `HK`, `SG`, `KR`, `TW`, `DE`, `GB`, `CA`, `FR` 等。
4. **第 4 层（代码已注释）：云服务商 / CDN 筛选（Cloud Providers）** 
   * 进一步精准狙击特定云环境或防护后的资产，如：`cloud_name="Aliyundun"`、`cloud_name="Cloudflare"` 等。

通过上述多维组合，程序会自动生成多个高精度的复合查询条件（例如：`body="xxx" && is_domain="false" && country="US"`），逐一向 FOFA 发起稳定、低频的探测与数据收集。

---

## ⚠️ 免责声明与特别说明

1. **个人使用声明**：本仓库的所有修改与优化，**仅用于个人的日常技术学习**。请勿将本工具用于任何非法用途或大规模违规网络爬取，产生的一切法律后果与责任均由使用者本人承担。
2. **侵权告知**：如果本项目中的任何内容、修改逻辑涉及侵权或不当之处，请随时通过 Issues 或其他方式指出，我将第一时间进行处理、修改或删除。

---


>Thanks to the contributors of this project

<table>
<tr>
    <td align="center">
        <a href="https://github.com/Cl0udG0d">
            <img src="https://avatars.githubusercontent.com/u/45556496?v=4" width="100;" alt="Cl0udG0d"/>
            <br />
            <sub><b>潘一二三</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/wanswu">
            <img src="https://avatars.githubusercontent.com/u/49047734?v=4" width="100;" alt="wanswu"/>
            <br />
            <sub><b>Wans</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/tastypear">
            <img src="https://avatars.githubusercontent.com/u/1382667?v=4" width="100;" alt="wanswu"/>
            <br />
            <sub><b>tastypear</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/KawaiiSh1zuku">
            <img src="https://avatars.githubusercontent.com/u/51824296?v=4" width="100;" alt="wanswu"/>
            <br />
            <sub><b>KawaiiSh1zuku</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/Valdo-Caeserius">
            <img src="https://avatars.githubusercontent.com/u/148833225?v=4" width="100;" alt="wanswu"/>
            <br />
            <sub><b>Valdo-Caeserius</b></sub>
        </a>
    </td>
    <td align="center">
        <a href="https://github.com/10cks">
            <img src="https://avatars.githubusercontent.com/u/47177550?v=4" width="100;" alt="wanswu"/>
            <br />
            <sub><b>10cks</b></sub>
        </a>
    </td>
<td align="center">
        <a href="https://github.com/fireinrain">
            <img src="https://avatars.githubusercontent.com/u/14249262?v=4" width="100;" alt="fireinrain"/>
            <br />
            <sub><b>fireinrain</b></sub>
        </a>
    </td>
</tr>
<tr>
<td align="center">
        <a href="https://github.com/Arc-2023">
            <img src="https://avatars.githubusercontent.com/u/64178177?v=4" width="100;" alt="fireinrain"/>
            <br />
            <sub><b>Arc-2023</b></sub>
        </a>
    </td>
</tr>
</table>


