You are orchestrating the analysis of an existing codebase to adapt Agent OS standards.

## Objective

Analyze the current project and update Agent OS standards to match the project's conventions and tech stack.

## Process

Delegate this analysis to the **project-analyzer** agent:

```
@.claude/agents/agent-os/project-analyzer.md

Analyze this project's codebase and adapt Agent OS standards.

Follow the analyze-codebase workflow to:
1. Scan project structure
2. Detect tech stack (languages, frameworks, dependencies)
3. Analyze code patterns and conventions
4. Generate analysis report
5. Offer to update Agent OS standards

After analysis, ask the user if they want to:
1. Auto-update standards
2. Review changes first
3. Skip updates

Reference workflow: @agent-os/workflows/analysis/analyze-codebase.md
```

## Expected Output

The agent should:
1. Create `agent-os/analysis-report.md` with comprehensive analysis
2. Optionally update standards in `agent-os/standards/`
3. Provide summary of findings and next steps

## After Completion

Output to user:

```
✅ Project analysis complete!

The project-analyzer agent has:
- Analyzed the codebase structure
- Detected tech stack and patterns
- Generated analysis report

Check `agent-os/analysis-report.md` for full details.

Next commands:
- `plan-product` - Document product mission and roadmap
- `shape-spec` - Start planning a new feature
```
