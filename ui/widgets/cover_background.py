#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Фоновое изображение с масштабированием cover (без искажений)."""

from kivy.uix.image import Image


def cover_background_image(source: str) -> Image:
    """
    Image, заполняющий родителя с сохранением пропорций (аналог CSS object-fit: cover).

    Центрируется автоматически; при смене размера окна пересчитывается через fit_mode.
    """
    return Image(
        source=source,
        fit_mode="cover",
        size_hint=(1, 1),
        pos_hint={"x": 0, "y": 0},
    )
