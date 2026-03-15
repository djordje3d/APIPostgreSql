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
            @update:model-value="form.vehicle_type_id = ($event as number | null) ?? ''"
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
              @userclick="imageInputRef?.click()"
            />
            <p class="text-sm text-slate-500">
              {{
                form.imageFile
                  ? `${form.imageFile.name} — will be resized before upload`
                  : t("entry.noFileChosen")
              }}
            </p>
            <button
              v-if="form.imageFile"
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
          :disabled="loading"
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
  vehicle_type_id: "" as number | "",
  garage_id: "" as number | "",
  spot_id: null as number | null,
  imageFile: null as File | null,
});
const imageInputRef = ref<HTMLInputElement | null>(null);
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

function close() {
  emit("update:modelValue", false);
  error.value = "";
  success.value = "";
}

function onImageChange(e: Event) {
  const input = e.target as HTMLInputElement;
  form.value.imageFile = input.files?.[0] ?? null;
}

function clearImage() {
  form.value.imageFile = null;
  if (imageInputRef.value) imageInputRef.value.value = "";
}

const MAX_IMAGE_DIM = 1200;
const JPEG_QUALITY = 0.85;

/** Resize image client-side to max 1200px and return as JPEG blob. */
function resizeImage(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
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
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas not supported"));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);
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
  form.value.garage_id = value ?? "";
  form.value.spot_id = null;
  onGarageChange();
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      loadOptions();
      form.value = {
        licence_plate: "",
        vehicle_type_id: "",
        garage_id: "",
        spot_id: null,
        imageFile: null,
      };
      clearImage();
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
    if (form.value.imageFile) {
      const blob = await resizeImage(form.value.imageFile);
      const { url } = await uploadTicketImage(blob, "ticket.jpg");
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
    const msg = (
      e as { response?: { data?: { detail?: string }; status?: number } }
    )?.response?.data?.detail;
    error.value = typeof msg === "string" ? msg : "Entry failed.";
  } finally {
    loading.value = false;
  }
}
</script>
