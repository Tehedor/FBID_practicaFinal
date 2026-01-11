MODE := local
KUBECTL := microk8s.kubectl

.PHONY: apply-0 delete-0 apply-1 delete-1 apply-2 delete-2 apply-3 delete-3 apply-4 delete-4 apply-5 delete-5 apply-6 delete-6 apply-7 delete-7 get-pods

# --- FUNCIÓN APPLY (Con soporte para .env) ---
# 1. Comprueba si el archivo existe.
# 2. Si existe .env, exporta las variables.
# 3. Usa envsubst para sustituir variables en el YAML.
# 4. Pasa el resultado a kubectl apply -f -
define apply_files
	@for f in $(1)*.yml $(1)*.yaml; do \
		if [ -f "$$f" ]; then \
			if [ -f .env ]; then \
				export $$(grep -v '^#' .env | xargs) && envsubst < $$f | $(KUBECTL) apply -f -; \
			else \
				$(KUBECTL) apply -f $$f; \
			fi; \
		fi; \
	done
endef

# --- FUNCIÓN DELETE (Con soporte para .env) ---
# Usamos envsubst también en delete por si usas variables 
# en el namespace o en nombres de recursos.
define delete_files
	@for f in $(1)*.yml $(1)*.yaml; do \
		if [ -f "$$f" ]; then \
			if [ -f .env ]; then \
				export $$(grep -v '^#' .env | xargs) && envsubst < $$f | $(KUBECTL) delete -f -; \
			else \
				$(KUBECTL) delete -f $$f; \
			fi; \
		fi; \
	done
endef

# --- TARGETS ---

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

apply-7:
	$(call apply_files,7)
delete-7:
	$(call delete_files,7)

get-pods:
	@$(KUBECTL) get pods -n spark-cluster

# Utilidad para limpiar todo en orden inverso (opcional)
delete-all: delete-7 delete-6 delete-5 delete-4 delete-3 delete-2 delete-1 delete-0