MODE := local
KUBECTL := microk8s.kubectl

.PHONY: apply-0 delete-0 apply-1 delete-1 apply-2 delete-2 apply-3 delete-3 apply-4 delete-4 apply-5 delete-5 apply-6 delete-6 get-pods

# Función para aplicar archivos por patrón
define apply_files
	@for f in $(1)*.yml; do \
		if [ -f "$$f" ]; then \
			$(KUBECTL) apply -f $$f; \
		fi; \
	done
endef

define delete_files
	@for f in $(1)*.yml; do \
		if [ -f "$$f" ]; then \
			$(KUBECTL) delete -f $$f; \
		fi; \
	done
endef

apply-0:
	$(call apply_files,0*$(MODE))
delete-0:
	$(call delete_files,0*$(MODE))

apply-1:
	$(call apply_files,1)
delete-1:
	$(call delete_files,1)

apply-2:
	$(call apply_files,2)
delete-2:
	$(call delete_files,2)

apply-3:
	$(call apply_files,3)
delete-3:
	$(call delete_files,3)

apply-4:
	$(call apply_files,4)
delete-4:
	$(call delete_files,4)

apply-5:
	$(call apply_files,5)
delete-5:
	$(call delete_files,5)

apply-6:
	$(call apply_files,6)
delete-6:
	$(call delete_files,6)

get-pods:
	@$(KUBECTL) get pods


delete-all: delete-0 delete-1 delete-2 delete-3 delete-4