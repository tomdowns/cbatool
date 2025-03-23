# Critical Programming Principles

## Core Development Principles
- **DRY** (Don't Repeat Yourself): Avoid duplicating code and functionality
- **KISS** (Keep It Simple, Stupid): Favor simple solutions over complex ones
- **YAGNI** (You Aren't Gonna Need It): Only implement what is currently needed
- **SOLID Principles**: Follow object-oriented design principles for maintainable code
  - **S**ingle Responsibility Principle: A class should have only one reason to change
  - **O**pen/Closed Principle: Open for extension, closed for modification
  - **L**iskov Substitution Principle: Subtypes must be substitutable for their base types
  - **I**nterface Segregation: Many client-specific interfaces better than one general-purpose interface
  - **D**ependency Inversion: Depend on abstractions, not concretions

## Git Workflow Principles
- **Feature Branch Workflow**: Develop each feature on a dedicated branch
- **Complete the Cycle**: Always finish one feature by merging back to develop before starting next
- **Regular Integration**: Keep feature branches up-to-date with develop
- **Small, Focused Changes**: Make incremental, atomic commits with descriptive messages
- **Proper Merging**: Use `--no-ff` to preserve feature branch history

## Development Process
- **Incremental Progress**: Make small, manageable changes rather than large refactorings
- **Consistent Implementation**: Follow established patterns and standards
- **Quality Assurance**: Maintain or improve code quality with each change
- **Documentation**: Keep track of all changes, decisions, and rationales

# Key Documents

## Project Structure and Core Components

1. **File Structure Documentation**
   - [docs/file-structure.txt](docs/current_file-structure.txt)
   - Provides overview of project organization and component structure

2. **Core Module Files**
   - [cbatool/core/data_loader.py](cbatool/core/data_loader.py)
   - [cbatool/core/analyzer.py](cbatool/core/analyzer.py)
   - [cbatool/core/depth_analyzer.py](cbatool/core/depth_analyzer.py)
   - [cbatool/core/position_analyzer.py](cbatool/core/position_analyzer.py)
   - [cbatool/core/base_analyzer.py](cbatool/core/base_analyzer.py)
   - [cbatool/core/visualizer.py](cbatool/core/visualizer.py)
   - [cbatool/core/position_visualizer.py](cbatool/core/position_visualizer.py)

3. **UI Components**
   - [cbatool/ui/app.py](cbatool/ui/app.py)
   - [cbatool/ui/widgets.py](cbatool/ui/widgets.py)
   - [cbatool/ui/dialogs.py](cbatool/ui/dialogs.py)

4. **Utility Modules**
   - [cbatool/utils/constants.py](cbatool/utils/constants.py)
   - [cbatool/utils/error_handling.py](cbatool/utils/error_handling.py)
   - [cbatool/utils/file_operations.py](cbatool/utils/file_operations.py)
   - [cbatool/utils/config_manager.py](cbatool/utils/config_manager.py)
   - [cbatool/utils/report_generator.py](cbatool/utils/report_generator.py)

5. **Entry Points**
   - [cbatool/\_\_main\_\_.py](cbatool/__main__.py)
   - [cbatool/\_\_init\_\_.py](cbatool/__init__.py)

## Development and Planning Documentation

1. **Improvement Plan**
   - [docs/improvement-plan.md](docs/improvement-plan.md)
   - Outlines the step-by-step plan for CBAtool Version 2.0

2. **Phase 2 Improvements**
   - [docs/phase2-improvements.md](docs/_archived/phase2-improvements.md)
   - Details for performance optimization and version control implementation

3. **Position Analysis Enhancements**
   - [Position Analysis Enhancements Implementation Guide.md](docs/position-Analysis-Enhancements-Implementation-Guide.md)
   - Implementation guide for the position analysis features

4. **Advanced Configuration System**
   - [Advanced Configuration System Summary.md](docs/advanced-Configuration-System-Summary.md)
   - Summary of the configuration management system implementation

5. **Git Branching Strategy**
   - [Git Branching Strategy.md](docs/Git-Branching-Strategy.md)
   - Guidelines for branching and merging strategy

6. **Development Progress and Next Steps**
   - [CBAtool Development Progress and Next Steps.md](docs/CBAtool-development-progress.md)
   - Current status and planned next steps

7. **Development Parking Document**
   - [CBAtool Development Parking Document.md](docs/CBAtool-parkingDoc.md)
   - Comprehensive document tracking development status and issues

8. **Development Workflow**
   - [cbatool-workflow.md](docs/cbatool-workflow.md)
   - Detailed workflow processes and templates


## Testing and Troubleshooting

1. **Troubleshooting Summary**
   - [docs/cbatool-troubleshooting-summary.md](docs/_Archived/cbatool-troubleshooting-summary.md)
   - Common issues and their resolutions


2. **Test Data and Scripts**
   - [generate_test_data.py](generate_test_data.py)
   - [test_imports.py](test_imports.py)
   - [test_core.py](cbatool/tests/test_core.py)

## User Documentation


1. **Detailed Documentation**
   - [docs/readme.md](docs/readme.md)
   - Comprehensive user documentation
