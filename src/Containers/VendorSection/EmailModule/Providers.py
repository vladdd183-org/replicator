"""Email module dependency injection providers.

Consolidated providers with clear scope separation.
"""

from dishka import Provider, Scope, provide

from src.Containers.VendorSection.EmailModule.Actions.SendEmailAction import SendEmailAction
from src.Containers.VendorSection.EmailModule.Tasks.SendEmailTask import SendEmailTask


class EmailModuleProvider(Provider):
    """Core provider for EmailModule - APP scope dependencies.

    Stateless services that can be reused across requests.
    """

    scope = Scope.APP

    # Tasks - stateless, reusable
    send_email_task = provide(SendEmailTask)


class EmailRequestProvider(Provider):
    """HTTP request-scoped provider for EmailModule."""

    scope = Scope.REQUEST

    # Actions
    send_email_action = provide(SendEmailAction)
