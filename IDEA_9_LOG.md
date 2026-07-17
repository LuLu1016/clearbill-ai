# Idea #9 — ClearBill AI: 完整讨论记录

从brainstorm list里的"9. 医疗账单多收费申诉助手"开始，到最终落地成demo仓库的全过程记录，按时间顺序整理。

---

## 1. Idea #9 首次出现（brainstorm候选列表）

在去掉idea #1（trading）之后，新增3个方向，其中第9个是：

> **9 | 医疗账单多收费申诉助手** | 49-80%的医疗账单含错误；$10K以上账单平均被多收$1,300；美国医生每年因账单错误损失$1250亿，医院损失$680亿；1亿美国人背负$2200亿医疗债；重复收费占错误账单的25%（[Medical Bill Rescue](https://medicalbillrescue.com/resources/medical-billing-errors-88-billion), [Aptarro](https://www.aptarro.com/insights/medical-billing-stats)）| **Gemini技术点**：多模态读账单+EOB，自动比对CPT代码识别重复/异常收费，生成申诉信 | **市场信号**：全美家庭级市场，1亿人受影响 | **就绪度**：✅ 数据极强（已有Resolve、Goodbill等玩家，但赛道仍很早期）

用户反馈："9看上去商业模式更好"，于是聚焦在这个方向上继续深挖。

---

## 2. User Experience + Presentation（产品设计）

### 产品名：ClearBill AI

### User Journey
1. **落地页**：「上传你的账单和EOB，60秒内帮你找出可能被多收的钱，我们已经发现平均每张$10K+账单被多收$1,300」
2. **上传**：两个文件框——① Itemized Bill（医院账单明细）② EOB（保险公司的Explanation of Benefits）。支持拍照或PDF。
3. **处理中动画**：显示Gemini正在做的事（"正在提取CPT代码…正在比对保险已批准金额…正在检测重复收费…"）
4. **结果页 / Billing Health Report**：
   - 顶部：总账单金额 vs 疑似多收金额
   - 下方逐条列出flag：日期、CPT code、问题类型、涉及金额、plain-language解释
   - 每条flag可展开看"证据"（账单原文截取 vs EOB原文截取并排对比）
5. **一键操作**：「生成申诉信」按钮 → Gemini基于flag出的具体项目生成申诉信
6. **（可选）分享卡片**：生成一张"我省了$XXX"的可分享卡片，用于GTM/social traction

### 3小时build分工建议
- 1人：Gemini prompt chain（structured extraction → cross-check reasoning → letter generation）
- 1人：前端上传+结果dashboard，部署到Cloud Run
- 1人：准备2-3份"干净"的demo样本账单 + backup
- 1人：one-pager + pitch稿 + 分享卡片视觉

### 现场Demo脚本
上传样本账单 → 现场处理（<20秒）→ 结果页显示"发现$340重复收费" → 点击生成申诉信 → 展示信件已写好可直接发送。不解说技术细节，强调"这是真实发生在1亿美国人身上的事"。

### One-Pager结构

| 板块 | 内容 |
|---|---|
| Problem | 49-80%医疗账单含错误；$10K+账单平均多收$1,300；1亿美国人背负$2200亿医疗债 |
| Insight | 患者没有工具/时间去比对账单和EOB逐行核对，医院也没有动力主动纠错 |
| Solution | 上传即出结果的AI审计+申诉信生成，不需要人工客服介入 |
| Why now | CFPB 2025年医疗债信用报告新规，公众对医疗账单议题关注度上升 |
| Market | 每年产生账单的1.5亿+参保美国人；对标Resolve/GoodBill这类人工审核服务 |
| Business model | Freemium，或按追回金额抽成（success fee模式） |
| Ask | 请求接入更多医院账单/EOB真实样本做fine-tune的合作意向 |

---

## 3. Demo材料从哪来

讨论了三个来源，按可信度排列：

1. **最强背书：真实医院的官方Chargemaster数据**——2021年CMS新规要求所有美国医院公开machine-readable的标准价格文件（[CMSgov/hospital-price-transparency GitHub](https://github.com/CMSgov/hospital-price-transparency)）。用Stanford Health Care自己公开的chargemaster，narrative上很巧妙："我们用Stanford Health Care自己法律要求公开的定价数据来验证你的账单"。
2. **最有真实感：找1-2个真实账单**——本人账单本人使用没有HIPAA问题，只需打码PII。
3. **补充素材：公开发表的真实案例数字**——NBC News报道的$177,300急诊账单案例（$16,000 CT scan，$1,000+ metabolic panel）用于one-pager叙事佐证。

---

## 4. 提取真实Stanford Health Care定价数据

下载了Stanford Health Care官方价格透明度文件：
`https://stanfordhealthcare.org/content/dam/SHC/patientsandvisitors/pricingtransparency/946174066_stanford-health-care_standardcharges.json`（147MB，75,208条记录，2026-04-01更新）

提取出的真实CPT价格（facility gross charge / 自费现金价）：

| CPT Code | 项目 | Gross Charge | Discounted Cash |
|---|---|---|---|
| 99285 | 急诊5级/创伤 | $15,270.00 | $6,108.00 |
| 99284 | 急诊4级 | $11,859.00 | $4,743.60 |
| 74177 | CT腹部+骨盆增强 | $17,197.00 | $6,878.80 |
| 71260 | CT胸部增强 | $10,126.00 | $4,050.40 |
| 70450 | CT头部平扫 | $7,777.00 | $3,110.80 |
| 80053 | 综合代谢检测组合 | $1,243.00 | $497.20 |
| 80048 | 基础代谢检测组合 | $1,035.00 | $414.00 |
| 85025 | CBC全血细胞计数 | $445.00 | $178.00 |
| 36415 | 静脉采血 | $112.00 | $44.80 |

构造的demo账单场景：急诊就诊(99285) + CT腹盆增强(74177) + 血检(85025+80053) + 静脉采血(36415)，总额约$35,414，藏两个可被抓出来的错误：①静脉采血重复收费两次（多收$112）②80053/80048同时收费的unbundling疑点（多收$1,035，**后来被判定不够可靠，见下一节**）。

---

## 5. Unbundling判定的可信度问题（重要修正）

用户提问："Unbundling违规是一个法律吗？还是有专业数据源判断？如何保证判定准确"

**结论**：不是法律，但有官方权威数据源——**CMS的NCCI（National Correct Coding Initiative）PTP edits**（Procedure-to-Procedure edits）和**MUE（Medically Unlikely Edits）**，每季度更新，明确列出哪两个CPT code不能同一天一起收费。这应该是产品架构里唯一可信的unbundling判断依据，而不是让模型凭自己的医学billing知识判断。

**但实际验证时发现障碍**：CMS官方PTP edit文件下载前必须先接受AMA（美国医学会）的CPT授权协议（`https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-procedure-procedure-ptp-edits`），没有替用户点击同意这个协议。因此：
- 之前推断的"80048+80053"配对**未经验证**，另有第三方培训材料提示真实配对可能是"80053+85025"，两者都未能在不接受AMA协议的情况下核实
- **最终决定**：demo里只保留100%站得住脚的"静脉采血重复收费"flag（不需要NCCI数据，纯账单内部逻辑）；unbundling flag从demo中去掉或改为"疑似unbundling，建议人工复核"的保守措辞
- 在one-pager里把"通过CMS NCCI PTP/MUE官方数据做grounding而非模型自由判断"写成技术差异化卖点，同时诚实标注"生产环境需要签署AMA CPT数据授权"作为已识别的合规事项

---

## 6. 提交/申诉渠道的现实情况

用户提问："提交那一步是每家医院自己的申诉网站吗？"

**结论**：不是，美国**没有统一标准化的医院账单申诉提交入口**。常见渠道：打电话给账单客服、邮寄纸质信件、传真、部分医院患者门户（如Stanford的MyHealth/Epic MyChart）的站内消息。保险相关申诉走保险公司自己的appeal流程，同样没有统一入口。

**对MVP的启示**：不要假装自动提交到医院系统（3小时内做不到，也没有可对接的API）。"生成申诉信"功能应该停在"生成可下载/可复制的申诉信文本+具体联系方式提示"，这也是Resolve、GoodBill等真实公司的实际做法（人工/用户自己寄送或打电话，没有一家做到自动API提交）。

---

## 7. 自动打电话/传真的可行性

用户提问："可以自动打电话/传真"

- **自动传真**：3小时内完全可行，用Fax API（Documo/mFax、Sfax、Notifyre等）几行代码接入，适合作为live demo的"wow moment"
- **自动打电话**：技术上可行（Gemini Live API + Twilio Voice API做外呼桥接），但live demo风险高（IVR菜单、通话质量不可控），建议不要在台上live打，改为**提前录一段成功案例剪进1分钟demo video**
- **合规提醒**：Stanford Health Care账单页本身就有"TCPA Billing Consent Process"专门页面，说明autodialed call在这行业是被监管的敏感操作；加州是双方同意录音州，AI外呼需要在开头明确告知"this call may be recorded"

---

## 8. 交付物：One-Pager + Demo代码 + GitHub

### One-Pager
`ClearBill_AI_OnePager.docx`（docx格式，可编辑），包含Problem/Insight/Solution/Proof（Stanford真实CPT价格表）/Why Now/Market/Business Model/Ask/Team（占位符待填）。

### Demo代码架构

```
Browser (templates/index.html, static/app.js)
   |  POST /api/analyze  (multipart: bill, eob)
   v
Flask (app.py)
   |  1. extract_line_items()     -> Gemini多模态，structured JSON输出
   |  2. find_duplicate_charges() -> 确定性Python逻辑，不依赖模型判断
   |  3. cross_check_eob()        -> 确定性Python逻辑
   |  4. check_unbundling()       -> 故意留空的stub（见第5节原因）
   |  5. draft_dispute_letter()   -> Gemini，只基于上面flag出的问题生成
   v
JSON response -> 前端渲染
```

- `demo_assets/sample_itemized_bill.pdf` + `sample_eob.pdf`：用真实Stanford CPT数据构造的合成demo文件（虚构患者，真实价格），账单里有重复收费的静脉采血，EOB显示保险公司已经把这条标记为denied duplicate
- `demo_assets/stanford_cpt_reference.json`：真实价格数据来源文档
- 已跑通冒烟测试：app能正常启动（无API key时不崩溃，给出清晰错误提示）、`find_duplicate_charges`和`cross_check_eob`单元测试通过
- `/api/send-fax`是明确标注的stub，未接入真实fax provider

### GitHub仓库
- https://github.com/LuLu1016/clearbill-ai （个人备份）
- https://github.com/LilChainyy/stanford_med （团队协作用这个，已推送全部代码+one-pager）

### 团队上下文Skill
`.claude/skills/clearbill-ai-context/SKILL.md`：打包了完整项目背景（评分标准、idea筛选框架、one-pager摘要、grounding的可信度边界、技术架构、待办事项），推送进两个仓库；同时打包了独立的`clearbill-ai-context.skill`文件可以单独分享。

---

## 待办事项清单

1. 团队成员姓名/角色——填进one-pager的Team部分
2. 真实Gemini API key——去 [AI Studio](https://aistudio.google.com/apikey) 拿一个配置到`.env`，目前完整pipeline还没有跑通真实Gemini调用
3. Auto-fax接入真实provider（建议在live demo前完成，是很强的现场展示点）
4. Auto-phone-call走pre-recorded视频路线，不要live demo
5. Unbundling检测——除非拿到真实验证过的NCCI数据，否则不要在demo/pitch里断言这个flag
