from ..common import ConfigClass

_info = """
This API service offers microservices through a RESTful interface and supports socket for ai_session. \
Please refer to the appropriate endpoint that aligns with your specific needs. \
Consult the API documentation or relevant resources to identify the correct endpoints for the functionalities you require.
""".strip()

class LandingPageModel:
    def __init__(self):
        self.name = ConfigClass.APP_NAME
        self.info = _info
        