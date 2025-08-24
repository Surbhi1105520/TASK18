Feature: Login & Logout (GUVI)

  Scenario: Successful login with valid credentials
    Given the user is on login page
    When the user logs in with username "surbXXXXX@gmail.com" and password "AXXX5"
    Then the user sees welcome banner for "Surbhi Singh"
    And the user logs out
    And the user is back on login page
