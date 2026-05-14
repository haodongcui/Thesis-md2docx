# Markdown Usage

Use `example/thesis-demo.md` as the canonical sample.

## Minimal Structure

```markdown
# 论文题目

## 封面信息
论文题目：你的论文题目
学生姓名：张三
学号：2022xxxxxx
所属院系：某某学院
专业：某某专业
班级：某某班
指导教师：某某老师
日期：2026 年 4 月

---

## 摘要
中文摘要正文。

关键词：关键词1；关键词2；关键词3

---

## ABSTRACT
English abstract.

KEY WORDS: Keyword one; Keyword two; Keyword three

---

## 目录
这里可以放占位文字；导出器会写入 Word 目录域。

---

# 1 绪论
## 1.1 研究背景
正文。

# 参考文献
[1] 作者. 文献题名[文献类型]. 出版信息.

# 致谢
致谢正文。
```

## Rules

- Front matter uses level-two headings such as `## 封面信息`, `## 摘要`, `## ABSTRACT`, and `## 目录`.
- Body starts at numbered level-one headings such as `# 1 绪论`.
- Use up to three heading levels for formal thesis sections.
- Put figure captions and table captions on their own lines, for example `图 2-1 xxx` and `表 2-1 xxx`.
- Use relative image paths such as `img/pipeline.png`.
- Use `:::figure-row` for side-by-side figures.
- Use `<!-- thesis-table-split: 8, 10 -->` between a table title and table when a long table needs continuation splits.
- Write citation markers as `[1]`, `[1-3]`, or `[1，3-4]`.
- Put references under `# 参考文献`.
- Put acknowledgement under `# 致谢`.
- Put appendices under `# 附录`.

## Formula Notes

- Inline formulas use `$...$`.
- Block formulas use `$$...$$`.
- Install the Node helper to convert LaTeX into Word OMML:

  ```bash
  npm install --prefix thesis_md2docx/math/latex2omml_node
  ```

- Without formula dependencies, export still succeeds and formulas fall back to LaTeX text.
