#include "engine/input.hpp"
#include "sokol_app.h"

namespace engine {

bool InputManager::is_mouse_locked() const {
    return sapp_mouse_locked();
}

void InputManager::set_mouse_locked(bool locked) {
    sapp_lock_mouse(locked);
    sapp_show_mouse(!locked);
}

InputManager::InputManager() {
    keys_down_.fill(false);
    keys_pressed_.fill(false);
    keys_released_.fill(false);
    mouse_down_.fill(false);
}

bool InputManager::is_key_down(Key key) const {
    auto idx = static_cast<size_t>(key);
    return (idx < MAX_KEYS) ? keys_down_[idx] : false;
}

bool InputManager::is_key_pressed(Key key) const {
    auto idx = static_cast<size_t>(key);
    return (idx < MAX_KEYS) ? keys_pressed_[idx] : false;
}

bool InputManager::is_key_released(Key key) const {
    auto idx = static_cast<size_t>(key);
    return (idx < MAX_KEYS) ? keys_released_[idx] : false;
}

bool InputManager::is_mouse_down(int button) const {
    return (button >= 0 && button < 8) ? mouse_down_[button] : false;
}

void InputManager::on_key_down(int keycode) {
    if (keycode >= 0 && static_cast<size_t>(keycode) < MAX_KEYS) {
        if (!keys_down_[keycode]) {
            keys_pressed_[keycode] = true;
        }
        keys_down_[keycode] = true;
    }
}

void InputManager::on_key_up(int keycode) {
    if (keycode >= 0 && static_cast<size_t>(keycode) < MAX_KEYS) {
        keys_down_[keycode] = false;
        keys_released_[keycode] = true;
    }
}

void InputManager::on_mouse_move(float x, float y, float dx, float dy) {
    mouse_x_ = x;
    mouse_y_ = y;
    mouse_dx_ += dx;
    mouse_dy_ += dy;
}

void InputManager::on_mouse_down(int button) {
    if (button >= 0 && button < 8) {
        mouse_down_[button] = true;
    }
}

void InputManager::on_mouse_up(int button) {
    if (button >= 0 && button < 8) {
        mouse_down_[button] = false;
    }
}

void InputManager::post_frame() {
    // Reset transient single-frame state
    keys_pressed_.fill(false);
    keys_released_.fill(false);
    mouse_dx_ = 0.0f;
    mouse_dy_ = 0.0f;
}

} // namespace engine
