# Created by josh at 9/1/17
Feature: The user can access page
  # Simple

  Scenario: The user can access the front page
    When the user navigates to the site
    Then the user sees the front page