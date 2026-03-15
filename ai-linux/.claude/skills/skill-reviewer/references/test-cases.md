# skill-reviewer テストケース

## 1. トリガーテスト

### Should trigger
- "skill-reviewerをレビューして"
- "このスキルの品質を確認して"
- "/skill-reviewer pdf-processing"
- "公開前にチェックして"
- "このスキルの改善点を教えて"
- "スキルの設計をレビューして"
- "skill-creatorを評価して"

### Should NOT trigger
- "新しいスキルを作って" (-> skill-creator)
- "エージェントをレビューして" (-> agent-reviewer)
- "CLAUDE.mdをレビューして" (-> agents-md-reviewer)
- "スキルの使い方を教えて"
- "コードをレビューして" (-> pr-reviewer)

## 2. 機能テスト

### Test 1: Normal review (well-structured skill)
```
Given: A skill with valid SKILL.md, references/, and scripts/
When: /skill-reviewer [skill-name]
Then:
  - All 4 phases evaluated
  - Each item marked with PASS/WARNING/FAIL
  - Summary includes problem counts by severity
  - Priority action list provided
```

### Test 2: Skill not found
```
Given: Non-existent skill name
When: /skill-reviewer nonexistent-skill
Then:
  - Similar names searched in .claude/skills/
  - User prompted to confirm correct name
```

### Test 3: Invalid frontmatter
```
Given: A skill with broken YAML frontmatter
When: /skill-reviewer [broken-skill]
Then:
  - YAML error reported as first FAIL
  - Remaining evaluation continues
```

### Test 4: No arguments
```
Given: No skill name provided
When: /skill-reviewer
Then:
  - AskUserQuestion used to confirm target
```

## 3. パフォーマンス比較

### Baseline (without skill)
- User must manually specify all check items
- Inconsistent evaluation criteria across reviews
- No structured output format

### With skill
- Consistent 4-phase evaluation
- Standardized PASS/WARNING/FAIL judgments
- Prioritized action list with concrete examples
- Interactive feedback loop
