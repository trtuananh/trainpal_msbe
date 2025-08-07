class ServiceRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'user_service':
            return 'user_service'
        elif model._meta.app_label == 'course_service':
            return 'course_service'
        elif model._meta.app_label == 'payment_service':
            return 'payment_service'
        elif model._meta.app_label == 'message_service':
            return 'message_service'
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'user_service':
            return 'user_service'
        elif model._meta.app_label == 'course_service':
            return 'course_service'
        elif model._meta.app_label == 'payment_service':
            return 'payment_service'
        elif model._meta.app_label == 'message_service':
            return 'message_service'
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return obj1._meta.app_label == obj2._meta.app_label

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'user_service':
            return db == 'user_service'
        elif app_label == 'course_service':
            return db == 'course_service'
        elif app_label == 'payment_service':
            return db == 'payment_service'
        elif app_label == 'message_service':
            return db == 'message_service'
        return db == 'default'
