import secrets


class Config(object):
    TESTING = False
    DEBUG = False
    SECRET_KEY = secrets.token_urlsafe(16)


class DevelopConfig(Config):
    DEBUG = True


class ProductConfig(Config):
    pass


envs = {
    "development": DevelopConfig,
    "product": ProductConfig
}
