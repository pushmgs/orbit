// Copyright (c) 2020 The Orbit Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef ORBIT_GL_THREAD_STATE_TRACK_H_
#define ORBIT_GL_THREAD_STATE_TRACK_H_

#include <GteVector.h>
#include <stdint.h>

#include <memory>
#include <string>

#include "CoreMath.h"
#include "ThreadBar.h"

namespace orbit_gl {

// This is a track dedicated to displaying thread states in different colors
// and with the corresponding tooltips.
// It is a thin sub-track of ThreadTrack, added above the callstack track (EventTrack).
// The colors are determined only by the states, not by the color assigned to the thread.

class ThreadStateTrack final : public ThreadBar {
 public:
  explicit ThreadStateTrack(OrbitApp* app, TimeGraph* time_graph, TimeGraphLayout* layout,
                            const CaptureData* capture_data, ThreadID thread_id,
                            CaptureViewElement* parent);

  void Draw(GlCanvas* canvas, PickingMode picking_mode, float z_offset) override;
  void UpdatePrimitives(Batcher* batcher, uint64_t min_tick, uint64_t max_tick,
                        PickingMode picking_mode, float z_offset) override;

  void OnPick(int x, int y) override;

  [[nodiscard]] bool IsEmpty() const override;

 private:
  std::string GetThreadStateSliceTooltip(Batcher* batcher, PickingId id) const;
};

}  // namespace orbit_gl

#endif  // ORBIT_GL_THREAD_STATE_TRACK_H_
