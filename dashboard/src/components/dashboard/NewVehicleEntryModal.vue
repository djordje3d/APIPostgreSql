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
      <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
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
import { listVehicleTypes } from "../../api/vehicleTypes";
import { listGarages } from "../../api/garages";
import { listSpots } from "../../api/spots";
import { getVehicleByPlate, createVehicle } from "../../api/vehicles";
import { ticketEntry } from "../../api/tickets";
import { uploadTicketImage } from "../../api/upload";
import { parseApiError } from "../../api/error";
import type { VehicleType } from "../../api/vehicleTypes";
import type { Garage } from "../../api/garages";
import type { Spot } from "../../api/spots";
import ButtonIn from "../ui/ButtonIn.vue";
import InputIn from "../ui/InputIn.vue";
import { useI18n } from "vue-i18n";

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

const imageInputRef = ref<HTMLInputElement | null>(null);
const imagePickGeneration = ref(0);
const imageProcessing = ref(false);
const imageError = ref("");
const vehicleTypes = ref<VehicleType[]>([]);
const garages = ref<Garage[]>([]);
const freeSpots = ref<Spot[]>([]);
const loading = ref(false);

const vehicleTypeOptions = computed(() =>
  vehicleTypes.value.map((vt) => ({ id: vt.id, label: vt.type })),
);
const garageOptions = computed(() =>
  garages.value.map((g) => ({ id: g.id, label: g.name })),
);
const spotOptions = computed(() =>
  freeSpots.value.map((s) => ({ id: s.id, label: s.code })),
);
const error = ref("");
const success = ref("");

const isImageReady = computed(() => !!form.value.resizedImageBlob);
const isFormFieldsReady = computed(() => {
  const plate = form.value.licence_plate.trim();
  return (
    !!plate &&
    form.value.vehicle_type_id !== null &&
    form.value.garage_id !== null
  );
});
const isCreateEntryReady = computed(() => isFormFieldsReady.value && isImageReady.value);

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

  // odmah prikaži naziv odabranog fajla
  form.value.ticketImageDisplayName = file.name;
  form.value.resizedImageBlob = null;
  imageProcessing.value = true;

  try {
    const blob = await resizeImage(file);

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

const MAX_IMAGE_DIM = 1200;
const JPEG_QUALITY = 0.85;

// blob is a binary large object that can be used to store images ready to be uploaded to the server.
/** Resize image client-side to max 1200px and return as JPEG blob. */
// return Promise<Blob> because the function is asynchronous and returns a promise.
// resolve is a function that is called when the promise is resolved.
// reject is a function that is called when the promise is rejected.
function resizeImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file); // create a temporary local URL from the file to load the image into the canvas.

    // internal browser URL that can be used to Image() object to load content from the file.
// 1. User chooses an image file 2. Browser creates a temporary local URL from the file 3. That URL is used to load the image into the canvas (memory). 

img.onload = () => {
      URL.revokeObjectURL(url);
      let { width, height } = img;
      if (width <= MAX_IMAGE_DIM && height <= MAX_IMAGE_DIM) {
        width = img.width; 
        height = img.height;
      } else {
        const r = Math.min(MAX_IMAGE_DIM / width, MAX_IMAGE_DIM / height);
        width = Math.round(width * r);
        height = Math.round(height * r);
      }
      const canvas = document.createElement("canvas"); // canvas is a HTML element that can be used to draw images. it is used to resize the image.
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas not supported"));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height); // draw the loaded image onto the canvas to resize it before converting to blob.
      
      // toBlob is a method that can be used to convert the canvas to a blob. it is used to convert the canvas to a blob.
      canvas.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))),
        "image/jpeg",
        JPEG_QUALITY,
      );
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Image load failed"));
    };
    img.src = url;
  });
}

// options for dropdowns lists, vehicle types and garages ...
async function loadOptions() {
  try {
    const [vtRes, gRes] = await Promise.all([
      listVehicleTypes({ limit: 100 }),
      listGarages({ limit: 100 }),
    ]);
    vehicleTypes.value = vtRes.data.items;
    garages.value = gRes.data.items;
  } catch {
    error.value = "Failed to load options";
  }
}

async function onGarageChange() {
  const gid = form.value.garage_id;
  if (!gid) {
    freeSpots.value = [];
    return;
  }
  try {
    const res = await listSpots({
      garage_id: gid,
      only_free: true,
      active_only: true,
      limit: 500,
    });
    freeSpots.value = res.data.items;
  } catch {
    freeSpots.value = [];
  }
}

function onGarageSelect(value: number | null) {
  form.value.garage_id = value ?? null;
  form.value.spot_id = null;
  onGarageChange();
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      loadOptions();
      imagePickGeneration.value += 1;
      imageProcessing.value = false;
      imageError.value = "";
      form.value = {
        licence_plate: "",
        vehicle_type_id: null,
        garage_id: null,
        spot_id: null,
        resizedImageBlob: null,
        ticketImageDisplayName: null,
      };
      if (imageInputRef.value) imageInputRef.value.value = "";
      freeSpots.value = [];
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
    let vehicleId: number;
    try {
      const byPlate = await getVehicleByPlate(plate);
      vehicleId = byPlate.data.id;
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } })?.response
        ?.status;
      if (status === 404) {
        const create = await createVehicle({
          licence_plate: plate,
          vehicle_type_id: vehicleTypeId,
        });
        vehicleId = create.data.id;
      } else throw e;
    }
    let imageUrl: string | undefined;
    if (form.value.resizedImageBlob) {
      const { url } = await uploadTicketImage(
        form.value.resizedImageBlob,
        "ticket.jpg",
      );
      imageUrl = url;
    }
    await ticketEntry({
      vehicle_id: vehicleId,
      garage_id: garageId,
      spot_id: form.value.spot_id ?? undefined,
      rentable_only: false,
      image_url: imageUrl ?? undefined,
    });
    success.value = "Entry created.";
    setTimeout(() => {
      emit("done");
    }, 800);
  } catch (e: unknown) {
    error.value = parseApiError(e, "Entry failed.").message;
  } finally {
    loading.value = false;
  }
}
</script>
