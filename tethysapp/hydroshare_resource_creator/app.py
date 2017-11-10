from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroshareResourceCreator(TethysAppBase):
    """
    Tethys app class for HydroShare Resource Creator.
    """

    name = 'HydroShare Resource Creator'
    index = 'hydroshare_resource_creator:home'
    icon = 'hydroshare_resource_creator/images/tool.svg'
    package = 'hydroshare_resource_creator'
    root_url = 'hydroshare-resource-creator'
    color = '#2ecc71'
    description = 'Create HydroShare resources using the CUAHSI HydroClient'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers for app.
        """

        url_map = url_map_maker(self.root_url)

        url_maps = (url_map(name='home',
                            url='hydroshare-resource-creator',
                            controller='hydroshare_resource_creator.controllers.home'),
                    url_map(name='create_resource',
                            url='hydroshare-resource-creator/create-resource',
                            controller='hydroshare_resource_creator.controllers_ajax.ajax_create_resource'),
                    url_map(name='login_callback',
                            url='hydroshare-resource-creator/login-callback',
                            controller='hydroshare_resource_creator.controllers.login_callback'),
                    url_map(name='login_test',
                            url='hydroshare-resource-creator/login-test',
                            controller='hydroshare_resource_creator.controllers_ajax.login_test'),
                    )

        return url_maps
