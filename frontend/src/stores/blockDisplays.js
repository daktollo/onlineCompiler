import { defineStore } from "pinia";

export const useBlockDisplaysStore = defineStore("blockDisplays", {
  state: () => ({
    byId: {},
  }),
  actions: {
    onDisplayCreate(payload) {
      const { display_id, size } = payload;
      console.log("[blockDisplays] display_create received:", payload);
      if (!display_id) return;
      if (!this.byId[display_id]) {
        const width = size?.width ?? 8;
        const height = size?.height ?? 8;
        const blocks = Array.from({ length: height }, () =>
          Array.from({ length: width }, () => ({
            color: [0, 0, 0],
            brightness: 1.0,
            on: true,
          }))
        );
        this.byId[display_id] = {
          displayId: display_id,
          width,
          height,
          blocks,
        };
        console.log(`[blockDisplays] created display ${display_id} (${width}x${height})`);
      }
    },
    onBlockUpdate(payload) {
      const { display_id, block_x, block_y, property, value } = payload;
      console.log("[blockDisplays] block_update received:", payload);
      const d = this.byId[display_id];
      if (!d) return;
      if (block_y < 0 || block_y >= d.height || block_x < 0 || block_x >= d.width) return;
      const cell = d.blocks[block_y][block_x];
      const before = { ...cell };
      if (property === "color") {
        cell.color = value;
      } else if (property === "brightness") {
        cell.brightness = value;
      } else if (property === "on") {
        cell.on = value;
      }
      console.log(
        `[blockDisplays] ${display_id}[${block_x},${block_y}] ${property}:`,
        before[property],
        "->",
        cell[property]
      );
    },
    reset() {
      this.byId = {};
    },
  },
});
