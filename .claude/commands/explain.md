# Explain Code - Understand and Document

Explain what's happening in a specific folder or file. This cookbook guides you through analyzing code, reading
documentation, and creating comprehensive explanations.

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
tree .
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

If you find gaps in documentation, create the missing README files

#### When to create a new README:

- Folder with multiple Python files but no README
- Complex component that needs dedicated explanation
- Standalone functionality within a scope
- Configuration or setup requirements not documented elsewhere
- Information from multiple files is worth aggregating and explaining on a higher level

### When to NOT create a new README:

- When the folder contains only very few files or just one file
- When the code is so easy to read that the developer should just read it themselves
- When the docstrings are so good that there is simply little of value to add

#### README Creation Process:

Create a new README in the appropriate location
Follow these documentation standards:

#### 📝 Writing Style for READMEs

- **Be VERY concise but complete**: Every word should add value
- **Write for your future self**: Assume you'll forget everything
- **Include "why" not just "what"**: Context matters

#### 🎯 Scope Rules for Documentation

- **Root README**: Platform-wide information only
- **Scope-level README**: Broad overview of the entire package
- **Subdirectory README**: Specific to that component
- **Deep folder README**: Very specific functionality
-

#### DOs and DONTs

- **DO** keep it as brief as possible. Documentation is hard to maintain, so we should keep it useful but minimal
- **DO** assume developers can just write the code themselves if they want to go into more details
- **DO** aggregate information from multiple files within a README
- **DO** Talk on a high-level: What are we trying to achieve here, why do we need that, what's the general philosophy
  and idea

- **DO NOT** Copy over code, as this is guaranteed to fall out of sync very quickly
- **DO NOT** include ANY markdown code blocks that show how this code can be imported or used. That is an indication
  that your documentation is too low-level
- **DO NOT** Talk on a low level about specific code files
- **DO NOT** simply state what is going on in the code - add higher level info and context
- **DO NOT** state the obvious or repeat what the docstring say
- **DO NOT** create a README just for one file. Documentation should live within the docstrings of the code itself!

### Step 6: Write Your Comprehensive Explanation

When you are done writing your README.md or decide that nor README.md must be edited or written, provide an in-depth
explanation to the user.

## You're Done When...

✅ You've read all relevant README files in the hierarchy  
✅ You understand the code's purpose and architecture  
✅ Missing README files have been created where needed  
✅ All documentation accurately reflects the current code  
✅ You can explain the code's role in the broader system  
✅ A new developer could understand the component from your explanation  
✅ You've documented any gotchas or important context you discovered

Remember: Good documentation is an investment in the future of the codebase and should smartly extend the code, not
explain it! 📖