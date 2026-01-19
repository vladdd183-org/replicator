"""Code generator engine for Hyper-Porto architecture.

Provides base generator class and utilities for generating code from Jinja2 templates.
Supports module generation, individual component generation, and template customization.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import logfire
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from rich.console import Console

console = Console()

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = Path(__file__).parent / "Templates"


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case.
    
    Args:
        name: String in PascalCase or camelCase
        
    Returns:
        String in snake_case
        
    Examples:
        >>> to_snake_case("UserModule")
        'user_module'
        >>> to_snake_case("createUser")
        'create_user'
    """
    # Insert underscore before uppercase letters
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_pascal_case(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase.
    
    Args:
        name: String in snake_case or kebab-case
        
    Returns:
        String in PascalCase
        
    Examples:
        >>> to_pascal_case("user_module")
        'UserModule'
        >>> to_pascal_case("create-user")
        'CreateUser'
    """
    # Handle already PascalCase
    if name[0].isupper() and "_" not in name and "-" not in name:
        return name
    
    # Split by underscore or hyphen
    parts = re.split(r"[_-]", name)
    return "".join(word.capitalize() for word in parts)


def pluralize(word: str) -> str:
    """Simple English pluralization.
    
    Args:
        word: Singular word
        
    Returns:
        Pluralized word
        
    Examples:
        >>> pluralize("user")
        'users'
        >>> pluralize("category")
        'categories'
    """
    if word.endswith("y") and not word.endswith(("ay", "ey", "iy", "oy", "uy")):
        return word[:-1] + "ies"
    elif word.endswith(("s", "sh", "ch", "x", "z")):
        return word + "es"
    else:
        return word + "s"


@dataclass
class GeneratorContext:
    """Context for template rendering.
    
    Contains all variables available in Jinja2 templates.
    
    Attributes:
        name: Entity name in PascalCase (e.g., "User", "BlogPost")
        name_lower: Entity name in lowercase (e.g., "user", "blogpost")
        name_snake: Entity name in snake_case (e.g., "user", "blog_post")
        name_plural: Pluralized name in lowercase (e.g., "users", "blog_posts")
        name_plural_pascal: Pluralized name in PascalCase (e.g., "Users", "BlogPosts")
        section: Section name (e.g., "AppSection")
        module_name: Full module name (e.g., "UserModule")
        with_graphql: Whether to include GraphQL resolvers
        with_websocket: Whether to include WebSocket handlers
        with_cli: Whether to include CLI commands
        with_workers: Whether to include background workers
        extra: Additional custom context variables
    """
    
    name: str
    section: str = "AppSection"
    with_graphql: bool = False
    with_websocket: bool = False
    with_cli: bool = False
    with_workers: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Calculate derived attributes."""
        # Ensure PascalCase
        self.name = to_pascal_case(self.name)
        
    @property
    def name_lower(self) -> str:
        """Entity name in lowercase."""
        return self.name.lower()
    
    @property
    def name_snake(self) -> str:
        """Entity name in snake_case."""
        return to_snake_case(self.name)
    
    @property
    def name_plural(self) -> str:
        """Pluralized name in snake_case."""
        return pluralize(self.name_snake)
    
    @property
    def name_plural_pascal(self) -> str:
        """Pluralized name in PascalCase."""
        return to_pascal_case(self.name_plural)
    
    @property
    def module_name(self) -> str:
        """Full module name (e.g., UserModule)."""
        return f"{self.name}Module"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for template rendering.
        
        Returns:
            Dictionary with all context variables
        """
        return {
            "name": self.name,
            "name_lower": self.name_lower,
            "name_snake": self.name_snake,
            "name_plural": self.name_plural,
            "name_plural_pascal": self.name_plural_pascal,
            "section": self.section,
            "module_name": self.module_name,
            "with_graphql": self.with_graphql,
            "with_websocket": self.with_websocket,
            "with_cli": self.with_cli,
            "with_workers": self.with_workers,
            **self.extra,
        }


@dataclass
class BaseGenerator:
    """Base class for code generators.
    
    Provides common functionality for generating code from Jinja2 templates.
    Subclasses implement specific generation logic.
    
    Attributes:
        ctx: Generator context with template variables
        templates_dir: Path to templates directory
        output_dir: Path to output directory
        env: Jinja2 environment
    """
    
    ctx: GeneratorContext
    templates_dir: Path = field(default_factory=lambda: TEMPLATES_DIR)
    output_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "src" / "Containers")
    env: Environment = field(init=False)
    
    def __post_init__(self) -> None:
        """Initialize Jinja2 environment."""
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        # Add custom filters
        self.env.filters["snake_case"] = to_snake_case
        self.env.filters["pascal_case"] = to_pascal_case
        self.env.filters["pluralize"] = pluralize
    
    def render_template(self, template_path: str) -> str:
        """Render a single template with context.
        
        Args:
            template_path: Relative path to template file
            
        Returns:
            Rendered template content
            
        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template = self.env.get_template(template_path)
        return template.render(**self.ctx.to_dict())
    
    def write_file(self, path: Path, content: str) -> None:
        """Write content to file, creating directories as needed.
        
        Args:
            path: Target file path
            content: File content to write
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logfire.info(f"Generated: {path}")
        console.print(f"  [green]✓[/green] {path.relative_to(PROJECT_ROOT)}")
    
    def file_exists(self, path: Path) -> bool:
        """Check if file already exists.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists
        """
        return path.exists()
    
    def generate(self) -> list[Path]:
        """Generate all files.
        
        Must be implemented by subclasses.
        
        Returns:
            List of generated file paths
        """
        raise NotImplementedError("Subclasses must implement generate()")


@dataclass
class ModuleGenerator(BaseGenerator):
    """Generator for complete Porto modules.
    
    Creates a full module structure including:
    - Actions (Create, Update, Delete)
    - Tasks
    - Queries (Get, List)
    - Data (Repository, Schemas, UnitOfWork)
    - Models (Entity, PiccoloApp)
    - UI (Controllers, Routes)
    - Events and Listeners
    - Errors
    - Providers
    
    Optionally includes:
    - GraphQL resolvers and types
    - WebSocket handlers
    - CLI commands
    - Background workers
    """
    
    def _get_module_path(self) -> Path:
        """Get base path for the module."""
        return self.output_dir / self.ctx.section / self.ctx.module_name
    
    def _get_template_files(self) -> list[tuple[str, str]]:
        """Get list of template files to generate.
        
        Returns:
            List of tuples (template_path, output_path)
        """
        name = self.ctx.name
        name_snake = self.ctx.name_snake
        
        files = [
            # Root files
            ("module/__init__.py.j2", "__init__.py"),
            ("module/Errors.py.j2", "Errors.py"),
            ("module/Events.py.j2", "Events.py"),
            ("module/Listeners.py.j2", "Listeners.py"),
            ("module/Providers.py.j2", "Providers.py"),
            
            # Actions
            ("module/Actions/__init__.py.j2", "Actions/__init__.py"),
            ("module/Actions/CreateAction.py.j2", f"Actions/Create{name}Action.py"),
            ("module/Actions/UpdateAction.py.j2", f"Actions/Update{name}Action.py"),
            ("module/Actions/DeleteAction.py.j2", f"Actions/Delete{name}Action.py"),
            
            # Tasks
            ("module/Tasks/__init__.py.j2", "Tasks/__init__.py"),
            
            # Queries
            ("module/Queries/__init__.py.j2", "Queries/__init__.py"),
            ("module/Queries/GetQuery.py.j2", f"Queries/Get{name}Query.py"),
            ("module/Queries/ListQuery.py.j2", f"Queries/List{self.ctx.name_plural_pascal}Query.py"),
            
            # Data
            ("module/Data/__init__.py.j2", "Data/__init__.py"),
            ("module/Data/Schemas/__init__.py.j2", "Data/Schemas/__init__.py"),
            ("module/Data/Schemas/Requests.py.j2", "Data/Schemas/Requests.py"),
            ("module/Data/Schemas/Responses.py.j2", "Data/Schemas/Responses.py"),
            ("module/Data/Repositories/__init__.py.j2", "Data/Repositories/__init__.py"),
            ("module/Data/Repositories/Repository.py.j2", f"Data/Repositories/{name}Repository.py"),
            ("module/Data/UnitOfWork.py.j2", "Data/UnitOfWork.py"),
            
            # Models
            ("module/Models/__init__.py.j2", "Models/__init__.py"),
            ("module/Models/Entity.py.j2", f"Models/{name}.py"),
            ("module/Models/PiccoloApp.py.j2", "Models/PiccoloApp.py"),
            ("module/Models/migrations/__init__.py.j2", "Models/migrations/__init__.py"),
            
            # UI/API
            ("module/UI/__init__.py.j2", "UI/__init__.py"),
            ("module/UI/API/__init__.py.j2", "UI/API/__init__.py"),
            ("module/UI/API/Controllers/__init__.py.j2", "UI/API/Controllers/__init__.py"),
            ("module/UI/API/Controllers/Controller.py.j2", f"UI/API/Controllers/{name}Controller.py"),
            ("module/UI/API/Routes.py.j2", "UI/API/Routes.py"),
        ]
        
        # Optional GraphQL
        if self.ctx.with_graphql:
            files.extend([
                ("module/UI/GraphQL/__init__.py.j2", "UI/GraphQL/__init__.py"),
                ("module/UI/GraphQL/Types.py.j2", "UI/GraphQL/Types.py"),
                ("module/UI/GraphQL/Resolvers.py.j2", "UI/GraphQL/Resolvers.py"),
            ])
        
        # Optional WebSocket
        if self.ctx.with_websocket:
            files.extend([
                ("module/UI/WebSocket/__init__.py.j2", "UI/WebSocket/__init__.py"),
                ("module/UI/WebSocket/Handlers.py.j2", "UI/WebSocket/Handlers.py"),
            ])
        
        # Optional CLI
        if self.ctx.with_cli:
            files.extend([
                ("module/UI/CLI/__init__.py.j2", "UI/CLI/__init__.py"),
                ("module/UI/CLI/Commands.py.j2", "UI/CLI/Commands.py"),
            ])
        
        # Optional Workers
        if self.ctx.with_workers:
            files.extend([
                ("module/UI/Workers/__init__.py.j2", "UI/Workers/__init__.py"),
                ("module/UI/Workers/Tasks.py.j2", "UI/Workers/Tasks.py"),
            ])
        
        return files
    
    def generate(self) -> list[Path]:
        """Generate complete module structure.
        
        Returns:
            List of generated file paths
        """
        module_path = self._get_module_path()
        generated: list[Path] = []
        
        console.print(f"\n[bold blue]Generating module:[/bold blue] {self.ctx.module_name}")
        console.print(f"[dim]Path: {module_path}[/dim]\n")
        
        for template_path, output_name in self._get_template_files():
            output_path = module_path / output_name
            
            # Skip if file exists
            if self.file_exists(output_path):
                console.print(f"  [yellow]⚠[/yellow] Skipped (exists): {output_path.relative_to(PROJECT_ROOT)}")
                continue
            
            try:
                content = self.render_template(template_path)
                self.write_file(output_path, content)
                generated.append(output_path)
            except TemplateNotFound as e:
                console.print(f"  [red]✗[/red] Template not found: {e}")
                logfire.error(f"Template not found: {e}")
        
        return generated


@dataclass
class ComponentGenerator(BaseGenerator):
    """Generator for individual Porto components.
    
    Generates single components like Actions, Tasks, Queries, etc.
    Can be used to add components to existing modules.
    
    Attributes:
        component_type: Type of component (action, task, query, controller, event)
        component_name: Name of the component (e.g., "CreateUser", "SendEmail")
    """
    
    component_type: str = "action"
    component_name: str = ""
    
    def _get_template_path(self) -> str:
        """Get template path for component type."""
        templates = {
            "action": "components/action.py.j2",
            "task": "components/task.py.j2",
            "sync_task": "components/sync_task.py.j2",
            "query": "components/query.py.j2",
            "controller": "components/controller.py.j2",
            "event": "components/event.py.j2",
            "listener": "components/listener.py.j2",
        }
        return templates.get(self.component_type, templates["action"])
    
    def _get_output_path(self) -> Path:
        """Get output path for generated component."""
        module_path = self.output_dir / self.ctx.section / self.ctx.module_name
        
        folders = {
            "action": "Actions",
            "task": "Tasks",
            "sync_task": "Tasks",
            "query": "Queries",
            "controller": "UI/API/Controllers",
            "event": "",  # Goes in Events.py
            "listener": "",  # Goes in Listeners.py
        }
        
        folder = folders.get(self.component_type, "")
        
        # Determine filename
        if self.component_type == "event":
            # Events go in Events.py - this case is special
            return module_path / "Events.py"
        elif self.component_type == "listener":
            return module_path / "Listeners.py"
        elif self.component_type == "controller":
            return module_path / folder / f"{self.component_name}Controller.py"
        elif self.component_type in ("task", "sync_task"):
            return module_path / folder / f"{self.component_name}Task.py"
        elif self.component_type == "query":
            return module_path / folder / f"{self.component_name}Query.py"
        else:  # action
            return module_path / folder / f"{self.component_name}Action.py"
    
    def generate(self) -> list[Path]:
        """Generate single component.
        
        Returns:
            List with generated file path
        """
        output_path = self._get_output_path()
        
        console.print(f"\n[bold blue]Generating {self.component_type}:[/bold blue] {self.component_name}")
        console.print(f"[dim]Path: {output_path}[/dim]\n")
        
        # Add component_name to context
        self.ctx.extra["component_name"] = self.component_name
        self.ctx.extra["component_name_snake"] = to_snake_case(self.component_name)
        
        # Check if file exists
        if self.file_exists(output_path):
            console.print(f"  [yellow]⚠[/yellow] File already exists: {output_path.relative_to(PROJECT_ROOT)}")
            console.print("  [dim]Use --force to overwrite[/dim]")
            return []
        
        try:
            content = self.render_template(self._get_template_path())
            self.write_file(output_path, content)
            return [output_path]
        except TemplateNotFound as e:
            console.print(f"  [red]✗[/red] Template not found: {e}")
            logfire.error(f"Template not found: {e}")
            return []


def generate_module(
    name: str,
    section: str = "AppSection",
    with_graphql: bool = False,
    with_websocket: bool = False,
    with_cli: bool = False,
    with_workers: bool = False,
) -> list[Path]:
    """Convenience function to generate a complete module.
    
    Args:
        name: Entity name (e.g., "Blog", "Product")
        section: Section name (default: "AppSection")
        with_graphql: Include GraphQL support
        with_websocket: Include WebSocket support
        with_cli: Include CLI commands
        with_workers: Include background workers
        
    Returns:
        List of generated file paths
    """
    ctx = GeneratorContext(
        name=name,
        section=section,
        with_graphql=with_graphql,
        with_websocket=with_websocket,
        with_cli=with_cli,
        with_workers=with_workers,
    )
    generator = ModuleGenerator(ctx=ctx)
    return generator.generate()


def generate_component(
    component_type: str,
    component_name: str,
    module_name: str,
    section: str = "AppSection",
) -> list[Path]:
    """Convenience function to generate a single component.
    
    Args:
        component_type: Type (action, task, query, controller, event)
        component_name: Component name (e.g., "CreateUser", "SendEmail")
        module_name: Target module name (e.g., "User")
        section: Section name (default: "AppSection")
        
    Returns:
        List of generated file paths
    """
    ctx = GeneratorContext(
        name=module_name,
        section=section,
    )
    generator = ComponentGenerator(
        ctx=ctx,
        component_type=component_type,
        component_name=component_name,
    )
    return generator.generate()
