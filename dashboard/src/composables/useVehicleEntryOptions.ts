import { computed, type Ref, ref } from "vue";
import { listVehicleTypes } from "../api/vehicleTypes";
import { listGarages } from "../api/garages";
import { listSpots } from "../api/spots";
import type { VehicleType } from "../api/vehicleTypes";
import type { Garage } from "../api/garages";
import type { Spot } from "../api/spots";

export interface VehicleEntryFormShape {
  garage_id: number | null;
  spot_id: number | null;
}

/**
 * Dropdown data and garage → free-spot loading for the new vehicle entry flow.
 */
export function useVehicleEntryOptions(form: Ref<VehicleEntryFormShape>) {
  const vehicleTypes = ref<VehicleType[]>([]);
  const garages = ref<Garage[]>([]);
  const freeSpots = ref<Spot[]>([]);
  const optionsError = ref("");

  const vehicleTypeOptions = computed(() =>
    vehicleTypes.value.map((vt) => ({ id: vt.id, label: vt.type })),
  );
  const garageOptions = computed(() =>
    garages.value.map((g) => ({ id: g.id, label: g.name })),
  );
  const spotOptions = computed(() =>
    freeSpots.value.map((s) => ({ id: s.id, label: s.code })),
  );

  async function loadVehicleTypesAndGarages() {
    try {
      const [vtRes, gRes] = await Promise.all([
        listVehicleTypes({ limit: 100 }),
        listGarages({ limit: 100 }),
      ]);
      vehicleTypes.value = vtRes.data.items;
      garages.value = gRes.data.items;
    } catch {
      optionsError.value = "Failed to load options";
    }
  }

  async function loadFreeSpotsForGarage(garageId: number | null) {
    if (!garageId) {
      freeSpots.value = [];
      return;
    }
    try {
      const res = await listSpots({
        garage_id: garageId,
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
    loadFreeSpotsForGarage(form.value.garage_id);
  }

  function resetSpots() {
    freeSpots.value = [];
  }

  return {
    vehicleTypes,
    garages,
    freeSpots,
    optionsError,
    vehicleTypeOptions,
    garageOptions,
    spotOptions,
    loadVehicleTypesAndGarages,
    loadFreeSpotsForGarage,
    onGarageSelect,
    resetSpots,
  };
}
