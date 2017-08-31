from behave import *

use_step_matcher("re")


@then("the user sees the front page")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@when("the user navigates to the site")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass