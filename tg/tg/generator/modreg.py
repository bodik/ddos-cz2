"""generator modules registry helper"""
#14:34 < pharook> import module_registry
#14:34 < pharook> @module_helper.register

registered_classes = []

def register(cls):
	if cls not in registered_classes:
		registered_classes.append(cls)
	return cls
