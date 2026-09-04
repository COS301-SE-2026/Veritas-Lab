## Testing Policy Document

### Software/Technology for Testing:

#### PyTest
Pytest was chosen as the Backend testing framework for the following reasons:
+ PyTest integrates well with Python and FastAPI, which are used to develop the Backend of the project.
+ PyTest is relatively simple and easy to use.
+ PyTest-cov allows the team to measure coverage and work towards the 85% coverage non-functional requirement.

#### Jest
Jest was chosen as the Frontend testing framework for the following reasons:
+ The team is familiar with Jest.
+ Jest integrates well with JavaScript/TypeScript and React-based applications.
+ Jest provides support for mocking, assertions and automated unit testing.
+ Jest allows the Frontend components and logic to be tested independently.

#### Playwright
Playwright was chosen as the End-to-End testing framework for the following reasons:
+ Playwright supports automated testing of complete user workflows through the application.
+ Playwright can test interactions between the Frontend and Backend, making it suitable for validating system integration.
+ Playwright supports multiple browsers, allowing the application to be tested across different browser environments.
+ Playwright integrates well with GitHub Actions, allowing End-to-End tests to be executed automatically as part of the CI pipeline.

### Testing:
#### Unit Testing
Unit tests should be done with PyTest for the Frontend and Jest for the Backend. Furthermore, all unit tests must achieve an 85% coverage. The strategy of unit testing used by the system is White-Box Unit Testing.

#### Integration Testing
Big bang integration.

#### End-to-End Testing
Playwright End-to-End Tests should be written for each use case and must pass before entering production.

### Environments:
#### Development
There is a testing environment available to engineers only.

#### Production
The production is automatically deployed.
