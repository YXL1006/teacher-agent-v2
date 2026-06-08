import streamlit as st
import json
import re
import fitz  # PyMuPDF
from docx import Document
from openai import OpenAI

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="教师作业批改助手 V2.0",
    page_icon="📚",
    layout="wide"
)

# ==================== 提示词模板 ====================
CHINESE_PROMPT = """你是一位具有30年教龄的资深中学语文教师，请批改以下关于朱自清《背影》的读后感。

评分规则（满分100分）：
1. 情感理解（40分）：是否准确理解文中父爱的深沉与儿子的愧疚、怀念。
2. 文本分析（20分）：是否引用原文具体词句（动作、语言、外貌）并加以分析。
3. 个人感悟（30分）：是否联系自身生活，写出真实具体的反思与共鸣。
4. 语言表达（10分）：语句通顺，结构完整。

学生作业：
{essay}

请严格输出以下JSON格式，不要添加任何其他文字：
{{
  "情感理解": {{"得分": 整数, "评语": "引用学生原文具体语句进行分析"}},
  "文本分析": {{"得分": 整数, "评语": "引用学生原文语句并分析"}},
  "个人感悟": {{"得分": 整数, "评语": "结合具体内容点评"}},
  "语言表达": {{"得分": 整数, "评语": "评价语言和结构"}},
  "总分": 整数,
  "总评": "温暖鼓励的总结，并提出改进建议"
}}"""

ENGLISH_PROMPT = """你是一位以英语为母语的专业写作教师，请批改以下英语作文。

请从语法、词汇、句子结构、拼写、连贯性五个方面找出错误或可改进之处。

学生作文：
{essay}

请严格输出以下JSON格式，不要添加其他文字：
{{
  "errors": {{
    "grammar": [{{"original": "原句", "correction": "修改后", "explanation": "错误原因"}}],
    "word_choice": [{{"original": "原词/短语", "suggestion": "建议替换", "reason": "原因"}}],
    "sentence_structure": [{{"original": "原句", "improved": "优化句", "reason": "原因"}}],
    "spelling": [{{"error": "拼写错误", "correct": "正确拼写"}}]
  }},
  "coherence": "关于连贯性的简短评语",
  "overall_comment": "整体评价",
  "revised_paragraph": "修正后的完整段落"
}}"""

MATH_PROMPT = """你是一位严谨的中学数学老师，请逐步检查以下解答题。

题目：
{question}

参考解法：
{reference}

学生解答：
{solution}

请判断每一步是否正确，定位错误步骤，分析错误原因，并给出正确解法。

请严格输出以下JSON格式，不要添加其他文字：
{{
  "is_correct": true/false,
  "error_step": "如果正确填‘无’，否则指明第几步或具体位置",
  "error_reason": "详细分析错误原因",
  "corrected_solution": "正确的完整解法"
}}"""

# ==================== 模型调用 ====================
def call_zhipu(prompt: str, api_key: str, model: str = "glm-4-flash") -> str:
    client = OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

# ==================== 文档解析 ====================
def extract_text(uploaded_file) -> str | None:
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.txt'):
            return uploaded_file.read().decode('utf-8')
        elif name.endswith('.docx'):
            doc = Document(uploaded_file)
            return '\n'.join([p.text for p in doc.paragraphs])
        elif name.endswith('.pdf'):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            return ''.join([page.get_text() for page in doc])
        else:
            return None
    except Exception as e:
        st.error(f"文档解析失败：{e}")
        return None

# ==================== UI 界面 ====================
st.title("📚 教师作业批改助手 V2.0")
st.caption("支持文档上传 · 多课程选择 · 多模型切换")

# 侧边栏
with st.sidebar:
    st.header("⚙️ 配置")
    subject = st.selectbox(
        "选择课程",
        ["语文（读后感）", "英语（作文）", "数学（解答题）"],
        key="subject"
    )
    model_choice = st.selectbox(
        "选择批改模型",
        ["glm-4-flash（快速）", "glm-4（准确）"],
        key="model"
    )
    st.divider()
    st.caption("💡 提示：批改多份同科作业后，可在底部生成学情报告")

# 作业输入区域
st.header("📝 提交作业")
input_method = st.radio("输入方式", ["直接输入文字", "上传文档"], horizontal=True)

essay_text = ""
math_question = ""
math_reference = ""

if "语文" in subject:
    if input_method == "上传文档":
        uploaded = st.file_uploader("支持 .txt / .docx / .pdf", type=["txt", "docx", "pdf"])
        if uploaded:
            essay_text = extract_text(uploaded)
            if essay_text:
                st.success(f"✅ 成功解析文档，共 {len(essay_text)} 字")
                with st.expander("预览提取内容"):
                    st.text(essay_text)
            else:
                st.error("❌ 不支持的文件格式或解析失败")
    else:
        essay_text = st.text_area("请粘贴《背影》读后感", height=200, placeholder="在此粘贴学生作业...")

elif "英语" in subject:
    if input_method == "上传文档":
        uploaded = st.file_uploader("支持 .txt / .docx / .pdf", type=["txt", "docx", "pdf"])
        if uploaded:
            essay_text = extract_text(uploaded)
            if essay_text:
                st.success(f"✅ 成功解析文档，共 {len(essay_text)} 字符")
                with st.expander("预览提取内容"):
                    st.text(essay_text)
            else:
                st.error("❌ 不支持的文件格式或解析失败")
    else:
        essay_text = st.text_area("请粘贴英语作文", height=200, placeholder="在此粘贴学生作文...")

elif "数学" in subject:
    if input_method == "上传文档":
        st.warning("数学批改暂不支持文档上传，请直接输入题目、参考解法和学生解答。")
    st.subheader("题目")
    math_question = st.text_area("请输入数学题目", height=100)
    st.subheader("参考解法（可选，帮助模型判断）")
    math_reference = st.text_area("请输入参考解法或关键步骤", height=100)
    st.subheader("学生解答")
    essay_text = st.text_area("请输入学生解答过程", height=200, placeholder="在此粘贴学生解题步骤...")

# 批改按钮
if st.button("🚀 开始批改", type="primary", use_container_width=True):
    api_key = st.secrets.get("ZHIPU_API_KEY", "")
    if not api_key:
        st.error("❌ 未检测到 ZHIPU_API_KEY，请在 .streamlit/secrets.toml 中配置")
    else:
        if "语文" in subject:
            if not essay_text:
                st.warning("⚠️ 请先输入或上传作业内容")
            else:
                prompt = CHINESE_PROMPT.format(essay=essay_text)
        elif "英语" in subject:
            if not essay_text:
                st.warning("⚠️ 请先输入或上传英语作文")
            else:
                prompt = ENGLISH_PROMPT.format(essay=essay_text)
        elif "数学" in subject:
            if not math_question or not essay_text:
                st.warning("⚠️ 请填写数学题目和学生解答")
            else:
                prompt = MATH_PROMPT.format(question=math_question, reference=math_reference, solution=essay_text)

        if prompt:
            with st.spinner("🤖 AI正在批改中..."):
                # 选择模型
                if "flash" in model_choice:
                    model_name = "glm-4-flash"
                else:
                    model_name = "glm-4"

                raw_response = call_zhipu(prompt, api_key, model_name)

                # 尝试从回复中提取JSON
                try:
                    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        st.success("✅ 批改完成！")

                        # 根据学科展示不同结果
                        if "语文" in subject:
                            # 评分卡片
                            cols = st.columns(4)
                            dimensions = ["情感理解", "文本分析", "个人感悟", "语言表达"]
                            for i, dim in enumerate(dimensions):
                                with cols[i]:
                                    score = result.get(dim, {}).get("得分", "N/A")
                                    st.metric(dim, f"{score}/40" if i==0 else f"{score}/30" if i==2 else f"{score}/20" if i==1 else f"{score}/10")
                            # 总分
                            st.metric("🎯 总分", f"{result.get('总分', 'N/A')}/100")
                            # 详细评语
                            st.subheader("💬 详细评语")
                            for dim in dimensions:
                                if dim in result:
                                    with st.expander(f"{dim}（{result[dim].get('得分', 'N/A')}分）"):
                                        st.write(result[dim].get("评语", "无"))
                            # 总评
                            if "总评" in result:
                                st.subheader("📝 总评")
                                st.info(result["总评"])

                        elif "英语" in subject:
                            st.subheader("🔍 错误详情")
                            errors = result.get("errors", {})
                            if errors:
                                tabs = st.tabs(["语法", "词汇", "句子结构", "拼写"])
                                err_types = ["grammar", "word_choice", "sentence_structure", "spelling"]
                                for tab, etype in zip(tabs, err_types):
                                    with tab:
                                        if etype in errors and errors[etype]:
                                            for item in errors[etype]:
                                                st.markdown(f"**原文：** {item.get('original', item.get('error', ''))}")
                                                st.markdown(f"**修改：** {item.get('correction', item.get('suggestion', item.get('improved', '')))}")
                                                st.markdown(f"*原因：{item.get('explanation', item.get('reason', ''))}*")
                                                st.divider()
                                        else:
                                            st.write("无此类错误")
                            st.subheader("📈 连贯性评价")
                            st.write(result.get("coherence", "无"))
                            st.subheader("✍️ 整体评价")
                            st.write(result.get("overall_comment", "无"))
                            st.subheader("🔧 修正后全文")
                            st.text_area("修正后段落", value=result.get("revised_paragraph", ""), height=200)

                        elif "数学" in subject:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("是否正确", "✅ 正确" if result.get("is_correct") else "❌ 错误")
                            with col2:
                                st.write(f"**错误步骤：** {result.get('error_step', '无')}")
                            st.write(f"**错误原因：** {result.get('error_reason', '无')}")
                            st.subheader("📐 正确解法")
                            st.write(result.get("corrected_solution", "无"))
                    else:
                        st.error("⚠️ 未能从模型回复中提取出JSON，请重试")
                        st.text("模型原始回复：")
                        st.text(raw_response)
                except Exception as e:
                    st.error(f"解析错误：{e}")
                    st.text("模型原始回复：")
                    st.text(raw_response)

# 学情报告（预留）
st.divider()
if st.button("📈 生成学情报告", use_container_width=True):
    st.info("学情报告功能：请先批改至少3份同科作业后使用此功能（后续版本将自动汇总历史批改数据）")