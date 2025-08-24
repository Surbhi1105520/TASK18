Feature: ZenClass Login & Logout (Allure)

  Background:
    Given the user is on login page

  @success
  Scenario Outline: Successful login with valid credentials
    When the user logs in with username "<username>" and password "<password>"
    Then the user sees the dashboard
    And the user logs out
    And the user is back on login page

    Examples:
      # Use a test account that does NOT trigger OTP/CAPTCHA.
      | username                     | password        |
      | surbhXXX@gmail.com | AvNNN5 |

  @failure
  Scenario Outline: Unsuccessful login with invalid credentials
    Examples:
      | username               | password     |
      | invalid@example.com    | wrongpass123 |

  @ui
  Scenario: Validate username and password input boxes
    Then the username input should be visible and editable
    And the password input should be visible and masked

  @ui
  Scenario: Validate submit button is visible and enabled
    Then the submit button should be visible and enabled

  @ui
  Scenario: Validate submit behavior with empty fields
    When the user clears login fields
    And the user clicks submit
    Then the login should fail and stay on login page
