# SAM "makefile" build method (template.yaml: BuildMethod: makefile).
#
# Both Lambdas ship the same artifact — the full vambora package plus its
# runtime deps — and differ only by their Handler. SAM invokes one target per
# function and expects the deployable tree in $(ARTIFACTS_DIR).
#
# Deps are pinned in lambda/requirements.txt (generated from the uv lock; CI
# checks it for drift). Build on an arm64 host so the installed wheels match
# the functions' arm64 architecture.

define build_lambda
	python -m pip install -r lambda/requirements.txt -t "$(ARTIFACTS_DIR)" --no-compile
	cp -r src/vambora "$(ARTIFACTS_DIR)/vambora"
	cp alembic.ini "$(ARTIFACTS_DIR)/alembic.ini"
endef

build-ApiFunction:
	$(build_lambda)

build-PollerFunction:
	$(build_lambda)

# Regenerate the pinned Lambda requirements from the uv lock.
.PHONY: lambda-requirements
lambda-requirements:
	uv export --no-dev --no-emit-project --no-hashes --no-annotate --no-header \
		> lambda/requirements.txt
