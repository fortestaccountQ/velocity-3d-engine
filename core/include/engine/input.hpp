#pragma once

#include <array>
#include <cstdint>

namespace engine {

enum class Key : int {
    Invalid = 0,
    Space = 32,
    Apostrophe = 39,
    Comma = 44,
    Minus = 45,
    Period = 46,
    Slash = 47,
    Num0 = 48, Num1 = 49, Num2 = 50, Num3 = 51, Num4 = 52,
    Num5 = 53, Num6 = 54, Num7 = 55, Num8 = 56, Num9 = 57,
    Semicolon = 59, Equal = 61,
    A = 65, B = 66, C = 67, D = 68, E = 69, F = 70, G = 71, H = 72,
    I = 73, J = 74, K = 75, L = 76, M = 77, N = 78, O = 79, P = 80,
    Q = 81, R = 82, S = 83, T = 84, U = 85, V = 86, W = 87, X = 88,
    Y = 89, Z = 90,
    Escape = 256, Enter = 257, Tab = 258, Backspace = 259,
    Right = 262, Left = 263, Down = 264, Up = 265,
    PageUp = 266, PageDown = 267, Home = 268, End = 269,
    LeftShift = 340, LeftControl = 341, LeftAlt = 342
};

class InputManager {
public:
    InputManager();

    bool is_key_down(Key key) const;
    bool is_key_pressed(Key key) const;
    bool is_key_released(Key key) const;

    bool is_mouse_down(int button) const;
    float mouse_x() const { return mouse_x_; }
    float mouse_y() const { return mouse_y_; }
    float mouse_dx() const { return mouse_dx_; }
    float mouse_dy() const { return mouse_dy_; }

    void on_key_down(int keycode);
    void on_key_up(int keycode);
    void on_mouse_move(float x, float y, float dx, float dy);
    void on_mouse_down(int button);
    void on_mouse_up(int button);

    void post_frame();

private:
    static constexpr size_t MAX_KEYS = 512;
    std::array<bool, MAX_KEYS> keys_down_{false};
    std::array<bool, MAX_KEYS> keys_pressed_{false};
    std::array<bool, MAX_KEYS> keys_released_{false};

    std::array<bool, 8> mouse_down_{false};
    float mouse_x_{0.0f};
    float mouse_y_{0.0f};
    float mouse_dx_{0.0f};
    float mouse_dy_{0.0f};
};

} // namespace engine
