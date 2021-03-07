"""
Copyright (c) 2020 The Orbit Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
"""

import logging
import time

from typing import Tuple, List, Iterable

from core.common_controls import Track
from core.orbit_e2e import E2ETestCase, E2ETestSuite
from pywinauto.base_wrapper import BaseWrapper
from pywinauto import mouse, keyboard


class CaptureWindowE2ETestCaseBase(E2ETestCase):
    """
    Base class for fragments interacting with the capture window, provides common functionality.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._time_graph = None

    def execute(self, suite: E2ETestSuite):
        self._time_graph = self.find_control('Image', name='TimeGraph', parent=suite.top_window())
        super().execute(suite=suite)

    def _find_tracks(self, name_contains: str = None):
        tracks = self._time_graph.children()
        if name_contains is not None:
            tracks = filter(lambda track: name_contains in track.texts()[0], tracks)
        return list(tracks)


class SelectTrack(CaptureWindowE2ETestCaseBase):
    """
    Select a track in the capture window and check the selection afterwards.
    """

    def _execute(self, track_index: int = 0, check_selection_before: bool = False, expect_failure: bool = False):
        """
        :param track_index: Index of the track to select
        :param check_selection_before: If True, verifies that this track was not selected before
        :param expect_failure: If True, it is expected that the track in question is NOT selected after executing this
        """
        track = Track(self._find_tracks()[track_index])

        if check_selection_before:
            self.expect_true(not track.container.has_keyboard_focus(), "Track is not selected")
        logging.info("Selecting track with index %s", track_index)
        track.title.click_input()
        if expect_failure:
            self.expect_true(not track.container.has_keyboard_focus(), "Track is not selected")
        else:
            self.expect_true(track.container.has_keyboard_focus(), "Track is selected")


class DeselectTrack(CaptureWindowE2ETestCaseBase):
    """
    Deselect the currently selected track in the capture window, verify no track is selected afterwards.
    Expects a track to be selected, fails otherwise.
    """

    def _find_focused_track_and_index(self) -> Tuple[BaseWrapper, int]:
        children = self._find_tracks()
        for i in range(len(children)):
            if children[i].has_keyboard_focus():
                return children[i], i
        return None, None

    def _execute(self):
        track, index = self._find_focused_track_and_index()

        self.expect_true(index is not None, "A track is selected")
        # Click slightly above the track to hit any empty space
        rect = track.rectangle()
        mouse.click(button='left', coords=(rect.left + 10, rect.top - 5))
        # TODO: I need to call this twice to work, why?
        mouse.click(button='left', coords=(rect.left + 10, rect.top - 5))
        self.expect_true(not self._find_tracks()[index].has_keyboard_focus(), "Track is no longer selected")
        self.expect_true(self._find_focused_track_and_index()[0] is None, "No Track is selected")


class MoveTrack(CaptureWindowE2ETestCaseBase):
    """
    Click and drag a track in the capture window, verify ordering of tracks afterwards.
    """

    def _execute(self, track_index: int = 0, new_index: int = 0, expected_new_index: int = None):
        """
        :param track_index: Track index (before dragging) to move
        :param new_index: New index the track should be moved to
        :param expected_new_index: Optional - Expected index of the track after moving. If None, it is expected that
            the track will be at position <new_index> after execution.
        """
        if expected_new_index is None:
            expected_new_index = new_index

        # Drag 1 px above the target track index if moving up, or 1 px below if moving down
        tracks = self._find_tracks()
        rect = tracks[new_index].rectangle()
        track_count = len(tracks)
        if track_index % track_count >= new_index % track_count:
            new_y = rect.top - 1
        else:
            new_y = rect.bottom + 1

        track = Track(tracks[track_index])
        mouse_x = track.title.rectangle().left + 5
        logging.info("Moving track '%s' from index %s to y=%s (expected new index: %s)",
                     track.container.texts()[0], track_index, new_y, expected_new_index)

        track.title.drag_mouse_input((mouse_x, new_y + 5))

        index = self._find_tracks().index(track.container)
        self.expect_eq(index, expected_new_index % track_count, "Expected track index after reordering")


class MatchTracks(CaptureWindowE2ETestCaseBase):
    """
    Verify that the existing visible tracks match the expected tracks
    """
    def _execute(self, expected_count: int = None, expected_names: List[str or Iterable[str]] = None,
                 allow_additional_tracks=False):
        """
        You need to pass either expected_track_count, or expected_name_list. If both are passed, they need to match
        w.r.t. expected number of tracks.
        :param expected_count: # of tracks to be visible
        :param expected_names: List of (partial) matching names of tracks to be visible.
            The name is a partial match, but the exact number of tracks is expected. Each entry in this list can either
            be a string or a list of strings. If an entry is a list of strings, the test expects at least on of the
            names to be matched (i.e. this is an "or" condition on multiple possible track names)
        :param allow_additional_tracks: If True, encountering additional tracks beyond the given list / number is not
            considered an error
        """
        assert (expected_count is not None or expected_names)
        if expected_count is not None and expected_names:
            assert (expected_count == len(expected_names))
        if expected_count is None:
            expected_count = len(expected_names)

        tracks = self._find_tracks()

        if not allow_additional_tracks:
            self.expect_eq(len(tracks), expected_count, "# of tracks matches %s" % expected_count)
        else:
            self.expect_true(len(tracks) >= expected_count, "# of tracks is at least %s" % expected_count)

        names_found = 0
        if expected_names:
            logging.info("Matching visible tracks against name list (%s)", expected_names)
            for name in expected_names:
                found = False
                for track in tracks:
                    track_name = track.texts()[0]
                    if self._match(name, track_name):
                        found = True
                        names_found += 1
                        break
                self.expect_true(found, "Found a match for track name '%s'" % str(name))

        if expected_names and not allow_additional_tracks:
            self.expect_eq(names_found, expected_count, "No additional tracks are found")

    @staticmethod
    def _match(expected_name: str or Iterable[str], found_name: str) -> bool:
        if isinstance(expected_name, str):
            return found_name in expected_name
        else:
            for option in expected_name:
                if found_name in option:
                    return True
        return False


class FilterTracks(CaptureWindowE2ETestCaseBase):
    """
    Set a filter in the capture tab, and verify either the amount of visible tracks or their names
    """

    def _execute(self, filter_string: str = "", expected_count: int = None, expected_names: List[str] = None,
                 allow_additional_tracks=False):
        """
        See MatchTracks._execute() for documentation.
        """
        toolbar = self.find_control("ToolBar", "CaptureToolBar")
        track_filter = self.find_control("Edit", "FilterTracks", parent=toolbar)

        logging.info("Setting track filter text: '%s'", filter_string)
        track_filter.set_focus()
        track_filter.set_edit_text('')
        # Using send_keys instead of set_edit_text directly because set_edit_text ignores the wait timings...
        keyboard.send_keys(filter_string)

        # Verify by re-using a MatchTracks Fragment
        match_tracks = MatchTracks(expected_count=expected_count, expected_names=expected_names,
                                   allow_additional_tracks=allow_additional_tracks)
        match_tracks.execute(self.suite)


class Capture(E2ETestCase):
    def _show_capture_window(self):
        logging.info('Showing capture window')
        self.find_control("TabItem", "Capture").click_input()

    def _set_capture_options(self, collect_thread_states: bool):
        capture_tab = self.find_control('Group', "CaptureTab")

        logging.info('Opening "Capture Options" dialog')
        capture_options_button = self.find_control('Button', 'Capture Options', parent=capture_tab)
        capture_options_button.click_input()
        
        capture_options_dialog = self.find_control('Window', 'Capture Options')

        collect_thread_states_checkbox = self.find_control('CheckBox', 'Collect thread states', parent=capture_options_dialog)
        if collect_thread_states_checkbox.get_toggle_state() != collect_thread_states:
            logging.info('Toggling "Collect thread states" checkbox')
            collect_thread_states_checkbox.click_input()

        logging.info('Saving "Capture Options"')
        self.find_control('Button', 'OK', parent=capture_options_dialog).click_input()

    def _take_capture(self, length_in_seconds: int):
        capture_tab = self.find_control('Group', "CaptureTab")
        toggle_capture_button = self.find_control('Button', 'Toggle Capture', parent=capture_tab)

        logging.info('Starting to capture for %s seconds', length_in_seconds)
        toggle_capture_button.click_input()
        time.sleep(length_in_seconds)
        logging.info('Stopping capture')
        toggle_capture_button.click_input()

    def _verify_existence_of_tracks(self):
        logging.info("Verifying existence of at least one track...")
        MatchTracks(expected_count=1, allow_additional_tracks=True).execute(self.suite)

    def _execute(self, length_in_seconds: int = 5, collect_thread_states: bool = False):
        self._show_capture_window()
        self._set_capture_options(collect_thread_states)
        self._take_capture(length_in_seconds)
        self._verify_existence_of_tracks()


class CheckThreadStates(CaptureWindowE2ETestCaseBase):
    def _execute(self, track_name_contains: str, expect_exists: bool = True):
        tracks = self._find_tracks(track_name_contains)
        self.expect_true(len(tracks) > 0, 'Found tracks matching %s' % track_name_contains)
        logging.info('Checking for thread states in %s tracks', len(tracks))
        for track in tracks:
            track = Track(track)
            if expect_exists:
                self.expect_true(track.thread_states is not None, 'Track %s has a thread state pane' % track.name)
            else:
                self.expect_true(track.thread_states is None, 'Track %s has a no thread state pane' % track.name)


class CheckTimers(CaptureWindowE2ETestCaseBase):
    def _execute(self, track_name_contains: str, expect_exists: bool = True):
        tracks = self._find_tracks(track_name_contains)
        self.expect_true(len(tracks) > 0, 'Found tracks matching "%s"' % track_name_contains)
        logging.info('Checking for timers in %s tracks', len(tracks))
        for track in tracks:
            track = Track(track)
            if expect_exists:
                self.expect_true(track.timers is not None, 'Track "%s" has timers pane' % track.name)
            else:
                self.expect_true(track.timers is None, 'Track "%s" has no timers pane' % track.name)


class CheckEvents(CaptureWindowE2ETestCaseBase):
    def _execute(self, track_name_contains: str, expect_exists: bool = True):
        tracks = self._find_tracks(track_name_contains)
        self.expect_true(len(tracks) > 0, 'Found tracks matching "%s"' % track_name_contains)
        logging.info('Checking for events in %s tracks', len(tracks))
        for track in tracks:
            track = Track(track)
            if expect_exists:
                self.expect_true(track.events is not None, 'Track "%s" has events pane' % track.name)
            else:
                self.expect_true(track.events is None, 'Track "%s" has no events pane' % track.name)
