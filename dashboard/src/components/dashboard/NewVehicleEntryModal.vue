<template>
  <Modal
    :model-value="modelValue"
    @update:model-value="close"
    :title="t('header.newVehicleEntry')"
  >
    <form @submit.prevent="submit">
      <div class="space-y-4">
        <InputIn
          id="licence_plate"
          v-model="form.licence_plate"
          :label="t('entry.licencePlate')"
          type="text"
          required
          placeholder="e.g. AB123CD"
        />
        <div>
          <StandardDropdown
            :label="t('entry.vehicleType')"
            :options="vehicleTypeOptions"
            :model-value="form.vehicle_type_id || null"
            :placeholder="t('entry.selectType')"
            :nullable="false"
            @update:model-value="
              form.vehicle_type_id = ($event as number | null) ?? null
            "
          />
        </div>
        <div>
          <StandardDropdown
            :label="t('entry.garage')"
            :options="garageOptions"
            :model-value="form.garage_id || null"
            :placeholder="t('entry.selectGarage')"
            :nullable="false"
            @update:model-value="onGarageSelect($event as number | null)"
          />
        </div>
        <div>
          <StandardDropdown
            :label="t('entry.spot')"
            :options="spotOptions"
            v-model="form.spot_id"
            :nullable="true"
            :null-option-label="t('entry.spotAutoAssign')"
          />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">
            {{ t("entry.ticketImage") }}
          </label>
          <input
            ref="imageInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            required
            class="sr-only"
            aria-hidden="true"
            tabindex="-1"
            @change="onImageChange"
          />
          <div class="mt-1 flex flex-wrap items-center gap-2">
            <ButtonIn
              id="chooseFileBtn"
              type="button"
              :label="t('entry.chooseFile')"
              variant="outline"
              :caption="t('entry.chooseFile')"
              :disabled="imageProcessing"
              @userclick="imageInputRef?.click()"
            />
            <p class="text-sm text-slate-500">
              <template v-if="form.ticketImageDisplayName && imageProcessing">
                {{ t("entry.imageProcessing") }}:
                {{ form.ticketImageDisplayName }}
              </template>

              <template
                v-else-if="form.ticketImageDisplayName && form.resizedImageBlob"
              >
                {{
                  t("entry.imageReady", { name: form.ticketImageDisplayName })
                }}
              </template>

              <template v-else>
                {{ t("entry.noFileChosen") }}
              </template>
            </p>
            <button
              v-if="imageProcessing || form.resizedImageBlob"
              type="button"
              class="text-sm text-slate-600 underline hover:text-slate-800"
              @click="clearImage"
            >
              {{ t("entry.clearImage") }}
            </button>
          </div>
        </div>
      </div>
      <p v-if="displayError" class="mt-2 text-sm text-red-600">
        {{ displayError }}
      </p>
      <p v-if="success" class="mt-2 text-sm text-green-600">{{ success }}</p>

      <div class="mt-6 flex justify-between gap-2">
        <ButtonIn
          id="cancelBtn"
          :label="t('entry.cancel')"
          variant="outline"
          @userclick="close"
          :caption="t('entry.cancel')"
        />
        <ButtonIn
          id="createEntryBtn"
          :label="t('entry.createEntry')"
          variant="primary"
          :disabled="loading || !isCreateEntryReady"
          @userclick="submit"
          :caption="t('entry.createEntry')"
        />
      </div>
    </form>
  </Modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Modal from "../ui/Modal.vue";
import StandardDropdown from "../ui/StandardDropdown.vue";
import { parseApiError } from "../../api/error";
import ButtonIn from "../ui/ButtonIn.vue";
import InputIn from "../ui/InputIn.vue";
import { useI18n } from "vue-i18n";
import { resizeImageToJpeg } from "../../utils/imageResize";
import { useVehicleEntryOptions } from "../../composables/useVehicleEntryOptions";
import { createParkingEntry } from "../../services/createParkingEntry";

const props = defineProps<{ modelValue: boolean }>();
const { t } = useI18n();
const emit = defineEmits(["update:modelValue", "done"]);

const form = ref({
  licence_plate: "",
  vehicle_type_id: null as number | null,
  garage_id: null as number | null,
  spot_id: null as number | null,

  /** Displayed immediately after file pick. */
  ticketImageDisplayName: null as string | null,

  /** JPEG blob after client resize; uploaded only on submit. */
  resizedImageBlob: null as Blob | null,
});

const {
  vehicleTypeOptions,
  garageOptions,
  spotOptions,
  optionsError,
  loadVehicleTypesAndGarages,
  onGarageSelect,
  resetSpots,
} = useVehicleEntryOptions(form);

const imageInputRef = ref<HTMLInputElement | null>(null);
const imagePickGeneration = ref(0);
const imageProcessing = ref(false);
const loading = ref(false);

const error = ref("");
const success = ref("");

const displayError = computed(() => error.value || optionsError.value);

const isImageReady = computed(() => !!form.value.resizedImageBlob);
const isFormFieldsReady = computed(() => {
  const plate = form.value.licence_plate.trim();
  return (
    !!plate &&
    form.value.vehicle_type_id !== null &&
    form.value.garage_id !== null
  );
});
const isCreateEntryReady = computed(
  () => isFormFieldsReady.value && isImageReady.value,
);

function close() {
  emit("update:modelValue", false);
  error.value = "";
  success.value = "";
}

async function onImageChange(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;

  error.value = "";
  success.value = "";

  if (!file) {
    form.value.resizedImageBlob = null;
    form.value.ticketImageDisplayName = null;
    imageProcessing.value = false;
    return;
  }

  imagePickGeneration.value += 1;
  const gen = imagePickGeneration.value;

  form.value.ticketImageDisplayName = file.name;
  form.value.resizedImageBlob = null;
  imageProcessing.value = true;

  try {
    const blob = await resizeImageToJpeg(file);

    if (gen !== imagePickGeneration.value) return;

    form.value.resizedImageBlob = blob;
  } catch {
    if (gen !== imagePickGeneration.value) return;

    form.value.resizedImageBlob = null;
    form.value.ticketImageDisplayName = null;
    input.value = "";
    error.value = t("entry.imageResizeFailed");
  } finally {
    if (gen === imagePickGeneration.value) {
      imageProcessing.value = false;
    }
  }
}

function clearImage() {
  imagePickGeneration.value += 1;
  form.value.resizedImageBlob = null;
  form.value.ticketImageDisplayName = null;
  imageProcessing.value = false;
  error.value = "";
  success.value = "";

  if (imageInputRef.value) {
    imageInputRef.value.value = "";
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      optionsError.value = "";
      loadVehicleTypesAndGarages();
      imagePickGeneration.value += 1;
      imageProcessing.value = false;
      form.value = {
        licence_plate: "",
        vehicle_type_id: null,
        garage_id: null,
        spot_id: null,
        resizedImageBlob: null,
        ticketImageDisplayName: null,
      };
      if (imageInputRef.value) imageInputRef.value.value = "";
      resetSpots();
    }
  },
);

async function submit() {
  error.value = "";
  success.value = "";
  const plate = form.value.licence_plate.trim();
  const vehicleTypeId = form.value.vehicle_type_id;
  const garageId = form.value.garage_id;
  if (!plate || !vehicleTypeId || !garageId) return;
  if (!form.value.resizedImageBlob) {
    error.value = t("entry.noFileChosen");
    return;
  }

  loading.value = true;
  try {
    await createParkingEntry({
      licencePlate: plate,
      vehicleTypeId,
      garageId,
      spotId: form.value.spot_id,
      imageBlob: form.value.resizedImageBlob,
      imageFileName: "ticket.jpg",
    });
    success.value = t("toast.vehicleCreated");
    setTimeout(() => {
      emit("done");
    }, 800);
  } catch (e: unknown) {
    error.value = parseApiError(e, t("entry.createFailed")).message;
  } finally {
    loading.value = false;
  }
}
</script>
