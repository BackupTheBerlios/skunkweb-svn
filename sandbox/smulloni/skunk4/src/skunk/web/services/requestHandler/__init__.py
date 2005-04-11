from skunk.web.config import Configuration

Configuration.mergeDefaults(DocumentTimeout=30,
                            PostResponseTimeout=20,
                            jobs=())


