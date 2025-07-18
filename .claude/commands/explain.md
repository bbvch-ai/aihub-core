# Explain Code - Understand and Document

Explain what's happening in a specific folder or file. This cookbook guides you through analyzing code, reading documentation, and creating comprehensive explanations.

## Overview

Here's your analysis process:
1. Navigate to $FOLDER
2. Read all existing README files hierarchically
3. Analyze the code structure and content
4. Identify documentation gaps
5. Create missing README files if needed
6. Provide a comprehensive explanation

## Your Code Analysis Cookbook

### Step 1: Navigate and Survey

Start by exploring the target location:

```bash
# Navigate to the folder you want to understand
cd $FOLDER

# Get an overview of the structure
ls -la

# If it's a single file, examine its location
ls -la $(dirname $FOLDER)
```

### Step 2: Read the Documentation Hierarchy

Follow our README-first documentation approach by reading all relevant README files:

- Start with the project root README
- Check the scope-level README (if $FOLDER is within a scope)
- Look for a README in the current directory
- Find all README files in subdirectories

### Step 3: Analyze the Code Structure

Now examine the actual code to understand what's happening:

### Step 4: The Critical Analysis Questions

As you examine the code and documentation, ask yourself:

#### 🔍 What is the primary purpose?
- What problem does this code solve?
- How does it fit into the larger system?
- What are the key responsibilities?

#### 🏗️ What is the architecture?
- How is the code organized?
- What are the main components/classes?
- What are the key dependencies?

#### 🔄 What are the key workflows?
- How does data flow through the system?
- What are the main entry points?
- What are the typical usage patterns?

#### 📋 What's missing from documentation?
- Are there README files where you'd expect them?
- Do existing READMEs accurately describe the code?
- What would have helped you understand faster?

### Step 5: Create Missing Documentation

If you find gaps in documentation, create the missing README files:

#### When to create a new README:
- Folder with multiple Python files but no README
- Complex component that needs dedicated explanation
- Standalone functionality within a scope
- Configuration or setup requirements not documented elsewhere

#### README Creation Process:

Create a new README in the appropriate location
Follow these documentation standards:

#### 📝 Writing Style for READMEs
- **Be concise but complete**: Every word should add value
- **Use examples liberally**: Show, don't just tell
- **Write for your future self**: Assume you'll forget everything
- **Include "why" not just "what"**: Context matters

#### 🏗️ Standard README Structure
Keep it consistent across the codebase:

1. **Title and Brief Description**
   ```markdown
   # Component Name
   Brief one-line description of what this component does.
   ```

2. **Purpose/Overview** (if needed)
   ```markdown
   ## Overview
   Explain the broader context and why this component exists.
   ```

3. **Usage/API** (if applicable)
   ```markdown
   ## Usage
   Show how to use this component with concrete examples.
   ```

4. **Configuration** (if any)
   ```markdown
   ## Configuration
   Document any configuration options or environment variables.
   ```

5. **Examples** (always helpful)
   ```markdown
   ## Examples
   Provide real-world usage examples.
   ```

6. **Troubleshooting** (if relevant)
   ```markdown
   ## Troubleshooting
   Common issues and their solutions.
   ```

#### 🎯 Scope Rules for Documentation
- **Root README**: Platform-wide information only
- **Scope-level README**: Broad overview of the entire package
- **Subdirectory README**: Specific to that component
- **Deep folder README**: Very specific functionality

### Step 6: Write Your Comprehensive Explanation

After analyzing and documenting, provide a thorough explanation covering:

#### Technical Overview
- What the code does at a high level
- How it fits into the overall system architecture
- Key dependencies and relationships

#### Implementation Details
- Main classes, functions, and their responsibilities
- Important algorithms or patterns used
- Data structures and their purposes

#### Usage Patterns
- How developers typically interact with this code
- Common use cases and workflows
- Integration points with other components

#### Notable Design Decisions
- Why certain approaches were chosen
- Trade-offs that were made
- Any constraints or limitations

#### Development Context
- How to work with this code
- Testing approaches
- Common pitfalls to avoid

### Documentation Quality Standards

Follow these rules religiously:

#### 📚 Content Guidelines
- **Accuracy**: Documentation must match the code exactly
- **Completeness**: Cover all public APIs and main concepts
- **Clarity**: Use simple language and clear examples
- **Maintenance**: Update docs when code changes

#### 🔄 Consistency Rules
- Use the same terminology across all documentation
- Follow the established README structure
- Maintain consistent formatting and style
- Link related documentation where appropriate

#### 🎯 Audience Considerations
- Write for developers familiar with the tech stack
- Assume basic knowledge of the domain
- Explain complex concepts with examples
- Provide context for architectural decisions

## The Golden Rules

1. **README-first approach** - Documentation should exist before confusion
2. **Code is the source of truth** - When docs conflict with code, fix the docs
3. **Hierarchical documentation** - Each level serves a specific purpose
4. **No documentation debt** - Create missing docs now, not later
5. **Examples are king** - Show concrete usage over abstract descriptions

## You're Done When...

✅ You've read all relevant README files in the hierarchy  
✅ You understand the code's purpose and architecture  
✅ Missing README files have been created where needed  
✅ All documentation accurately reflects the current code  
✅ You can explain the code's role in the broader system  
✅ A new developer could understand the component from your explanation  
✅ You've documented any gotchas or important context you discovered

Remember: Good documentation is an investment in the future of the codebase! 📖