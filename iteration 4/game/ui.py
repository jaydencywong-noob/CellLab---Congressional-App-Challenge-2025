import pygame
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SILVER, LIGHT_BLUE, DARK_BLUE, BROWN, GRAY, AMINO_ACID_BOOST_TYPE, ORGANELLE_DATA, PROTEIN_DATA, TYPE_CODON_MAP, CHUNK_SIZE
from config import WORLD_BOUNDS
from upgrade import BuyableProteinUpgrade, OrganelleUpgrade, craft_protein, buy_protein, buy_organelle, CraftedProteinUpgrade, generate_protein_boosts, generate_protein_name, generate_protein_desc
from world_generation import ChunkState
import webbrowser

pygame.init()

def blur_surface(surface, amount=4):
    scale = 1.0 / amount
    surf_size = surface.get_size()
    scaled_down = pygame.transform.smoothscale(surface, (int(surf_size[0]*scale), int(surf_size[1]*scale)))
    blurred = pygame.transform.smoothscale(scaled_down, surf_size)
    return blurred

def render_text_fit(font, text, max_width, max_height, color):
    """Render text scaled down to fit within max_width and max_height."""
    size = font.get_height()
    test_font = font
    txt_surf = test_font.render(text, True, color)
    while (txt_surf.get_width() > max_width or txt_surf.get_height() > max_height) and size > 8:
        size -= 1
        #lazy way to grab font since apparently there isn't pygame.font.Font.get_name(), idk why
        test_font = pygame.font.SysFont("calibri", size)
        txt_surf = test_font.render(text, True, color)
    return txt_surf

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines

class Button:
    def __init__(self, rect, text, callback, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.hovered = False

    def draw(self, surface):
        color = LIGHT_BLUE if self.hovered else DARK_BLUE
        pygame.draw.rect(surface, color, self.rect)
        # Use the new helper to fit text
        txt_surf = render_text_fit(self.font, self.text, self.rect.width - 8, self.rect.height - 8, SILVER)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class ImageButton:
    """Button with an image instead of text"""
    def __init__(self, rect, image, callback, tooltip=""):
        self.rect = pygame.Rect(rect)
        self.image = image
        self.callback = callback
        self.tooltip = tooltip
        self.hovered = False
        self.font = pygame.font.SysFont("calibri", 12)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

    def draw(self, screen):
        # Draw button background
        color = LIGHT_BLUE if self.hovered else DARK_BLUE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, SILVER, self.rect, 2)
        
        # Draw image centered in button
        if self.image:
            image_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, image_rect)
        
        # Draw tooltip on hover
        if self.hovered and self.tooltip:
            tooltip_surface = self.font.render(self.tooltip, True, (255, 255, 255))
            tooltip_rect = tooltip_surface.get_rect()
            tooltip_rect.midtop = (self.rect.centerx, self.rect.bottom + 5)
            
            # Background for tooltip
            bg_rect = tooltip_rect.inflate(4, 2)
            pygame.draw.rect(screen, (40, 40, 40), bg_rect)
            pygame.draw.rect(screen, (200, 200, 200), bg_rect, 1)
            
            screen.blit(tooltip_surface, tooltip_rect)

class TextBox:
    def __init__(self, rect: pygame.Rect, font, placeholder="", filter=None, upper=False):
        self.rect = rect
        self.font = font
        self.text = ""
        self.placeholder = placeholder
        self.upper = upper
        self.filter = filter
        self.focused = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_interval = 500  # ms

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)

        if not self.focused or event.type != pygame.KEYDOWN:
            return None

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return "typing"
        elif event.key == pygame.K_RETURN:
            return None
        elif event.unicode.isprintable():
            if not self.filter or event.unicode.lower() in self.filter:
                if self.upper:
                    self.text += event.unicode.upper()
                else:
                    self.text += event.unicode
                return "typing"
        return None

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer %= self.cursor_interval

    def draw(self, surf):
        # 1) Draw background and border
        pygame.draw.rect(surf, (60,60,60), self.rect)
        border_color = LIGHT_BLUE if self.focused else GRAY
        pygame.draw.rect(surf, border_color, self.rect, 2)

        # 2) Choose display text and color
        display = self.text if self.text else self.placeholder
        color   = SILVER if self.text else (150,150,150)

        # 3) Render full-text surface
        txt_surf = self.font.render(display, True, color)
        text_w, text_h = txt_surf.get_size()

        # 4) Compute available width inside the box (accounting for padding)
        padding_x = 5
        padding_y = 5
        available_w = self.rect.width - padding_x * 2

        # 5) Determine left-crop offset so the end of text stays visible
        if text_w > available_w:
            crop_x = text_w - available_w
        else:
            crop_x = 0

        # 6) Blit only the rightmost slice of the text surface
        surf.blit(
            txt_surf,
            (self.rect.x + padding_x, self.rect.y + padding_y),
            area=pygame.Rect(crop_x, 0, available_w, text_h)
        )

        # 7) Draw caret at the logical end of the (possibly cropped) text
        if self.focused and self.cursor_visible:
            # caret x = box left + padding + min(text_w, available_w)
            caret_x = self.rect.x + padding_x + min(text_w, available_w)
            caret_y = self.rect.y + padding_y
            caret_h = self.font.get_height()
            pygame.draw.line(
                surf, SILVER,
                (caret_x, caret_y),
                (caret_x, caret_y + caret_h)
            )

class TextPanel:
    def __init__(self, rect, font, content, bg_color=(40,40,40), border_color=(71,86,87), padding=10, icon=None):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.content = content  # list of dicts: {"text": str, ...}
        self.bg_color = bg_color
        self.border_color = border_color
        self.padding = padding
        self.icon = icon
        self.scroll_offset = 0  # in lines
        self._wrapped_lines = []
        self._rebuild_wrapped_lines()

    def set_content(self, content):
        self.content = content
        self._rebuild_wrapped_lines()
        self.scroll_offset = 0

    def set_icon(self, icon):
        self.icon = icon

    def _rebuild_wrapped_lines(self):
        self._wrapped_lines = []
        max_w = self.rect.width - 2*self.padding - (50 if self.icon else 0)
        for entry in self.content:
            text = entry.get("text", "")
            color = entry.get("color", (198,197,185))
            font = entry.get("font", self.font)
            lines = wrap_text(text, font, max_w)
            for line in lines:
                self._wrapped_lines.append((line, color, font))

    def handle_event(self, event):
        # Only scroll if mouse is over the panel
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            visible_lines = (self.rect.height - 2*self.padding) // self.font.get_linesize()
            max_scroll = max(0, len(self._wrapped_lines) - visible_lines)
            if event.button == 4:  # scroll up
                self.scroll_offset = max(self.scroll_offset - 1, 0)
            elif event.button == 5:  # scroll down
                self.scroll_offset = min(self.scroll_offset + 1, max_scroll)

    def draw(self, surface, delta_time):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        icon_offset = 0
        if self.icon:
            icon_rect = self.icon.get_rect()
            icon_x = self.rect.x + self.rect.width - icon_rect.width - self.padding
            icon_y = self.rect.y + self.padding
            surface.blit(self.icon, (icon_x, icon_y))
            icon_offset = icon_rect.width + self.padding

        x = self.rect.x + self.padding
        y = self.rect.y + self.padding
        max_h = self.rect.height - 2*self.padding
        line_height = self.font.get_linesize()
        visible_lines = max_h // line_height

        # Only draw visible lines
        lines_to_draw = self._wrapped_lines[self.scroll_offset:self.scroll_offset + visible_lines]
        for i, (line, color, font) in enumerate(lines_to_draw):
            line_y = y + i * line_height
            txt_surf = font.render(line, True, color)
            surface.blit(txt_surf, (x, line_y))

        # If no content, show placeholder
        if not self._wrapped_lines:
            placeholder = "Nothing selected"
            txt_surf = self.font.render(placeholder, True, (120,120,120))
            surface.blit(txt_surf, (x, y + max_h//2 - line_height//2))

class GameUI:
    def __init__(self, screen, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont("calibri", 20)

    def draw(self, delta_time):
        # Calculate stats area dimensions
        from main import player_molecules
        stats_height = 34 + len(player_molecules) * 24 + 10  # FPS + molecules + padding
        stats_rect = pygame.Rect(5, 5, 280, stats_height)
        
        # Draw semi-transparent background for stats
        stats_surface = pygame.Surface((stats_rect.width, stats_rect.height))
        stats_surface.set_alpha(180)  # Semi-transparent
        stats_surface.fill((40, 40, 60))  # Dark blue-gray background
        self.screen.blit(stats_surface, stats_rect)
        
        # Draw border
        pygame.draw.rect(self.screen, SILVER, stats_rect, 2)
        
        # Draw FPS
        fps_text = f"FPS: {int(1.0 / delta_time) if delta_time > 0 else 0}"
        surf = self.font.render(fps_text, True, SILVER)
        self.screen.blit(surf, (10, 10))

        # Draw centralized molecule inventory
        x, y = 10, 34
        for mol_type, count in player_molecules.items():
            text = f"{mol_type.replace('_', ' ').title()}: {count}"
            surf = self.font.render(text, True, SILVER)
            self.screen.blit(surf, (x, y))
            y += 24

        # #Attributes
        # x, y = 10, 250
        # line_height = self.font.get_height()
        # # Display attributes in consistent order
        # attr_order = ['Strength', 'Dexterity', 'Endurance', 'Intelligence']
        # for i, attr in enumerate(attr_order):
        #     value = self.player.attributes[attr]
        #     text = f"{attr}: {value}"
        #     text_surf = self.font.render(text, True, (255, 255, 255))  # white color
        #     self.screen.blit(text_surf, (x, y + i * line_height))

class CellManagerUI:
    """Scrollable manager of cell groups. Groups expand on hover to show cells."""
    def __init__(self, rect: pygame.Rect, font, groups_ref: dict, selected_entities_ref):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.groups = groups_ref  # dict: name -> [cells]
        self.selected_entities = selected_entities_ref
        self.scroll_px = 0
        self.line_h = self.font.get_linesize()
        self.hover_group_key = None
        self.sticky_open_group = None  # keep expanded while hovering over its cells
        self.rename_group_key = None
        self.rename_box = None  # TextBox used for rename
        self.row_padding = 6
        self.close_w = 16

    def _visible_area(self):
        title_h = self.line_h + 8
        list_top = self.rect.y + title_h
        list_h = self.rect.height - title_h - 6
        return list_top, list_h

    def _iter_layout(self, available_w):
        """Yield layout items with y, h, type ('group' or 'cell'), and keys."""
        y = 0
        for name, cells in self.groups.items():
            text_w = available_w - self.close_w - 10
            lines = wrap_text(name, self.font, text_w)
            gh = max(self.line_h, len(lines) * self.line_h) + self.row_padding
            yield {'type': 'group', 'key': name, 'y': y, 'h': gh, 'lines': lines, 'cells': cells}
            y += gh
            if name == self.hover_group_key or name == self.sticky_open_group:
                # Expand: list cells
                for idx, cell in enumerate(cells):
                    ch = self.line_h + 2
                    yield {'type': 'cell', 'group': name, 'cell': cell, 'index': idx, 'y': y, 'h': ch}
                    y += ch
        yield {'total_h': y}

    def handle_event(self, event):
        handled = False
        list_top, list_h = self._visible_area()
        inner_w = self.rect.width - 12

        # Update hover on mouse motion
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                mx, my = event.pos
                my_rel = my - list_top + self.scroll_px
                new_hover = None
                last_group = None
                for item in self._iter_layout(inner_w):
                    if item.get('type') == 'group':
                        last_group = item['key']
                        if item['y'] <= my_rel < item['y'] + item['h']:
                            new_hover = item['key']
                    elif item.get('type') == 'cell' and self.hover_group_key in (item['group'], self.sticky_open_group):
                        # If moving into cell rows of the currently open group, keep it open
                        if item['y'] <= my_rel < item['y'] + item['h']:
                            new_hover = item['group']
                # Update hover and sticky group
                if new_hover:
                    self.hover_group_key = new_hover
                    self.sticky_open_group = new_hover
                else:
                    # Keep current sticky group while inside header area; do not collapse here
                    pass
            else:
                # Collapse when moving outside the panel
                self.hover_group_key = None
                self.sticky_open_group = None

        # Scroll wheel
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_px = max(0, self.scroll_px - event.y * 30)
                handled = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if self.rect.collidepoint(event.pos):
                delta = -30 if event.button == 4 else 30
                self.scroll_px = max(0, self.scroll_px + delta)
                handled = True

        # Interactions
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3) and self.rect.collidepoint(event.pos):
            mx, my = event.pos
            # Title row consumes nothing; compute relative Y inside list
            my_rel = my - list_top + self.scroll_px
            # Hit test layout
            for item in self._iter_layout(inner_w):
                if 'type' not in item:
                    break
                if not (item['y'] <= my_rel < item['y'] + item['h']):
                    continue
                if item['type'] == 'group':
                    # Check delete 'x' region
                    gx = self.rect.x + self.rect.width - self.close_w - 6
                    gy = list_top + item['y'] - self.scroll_px
                    close_rect = pygame.Rect(gx, gy + 4, self.close_w, self.line_h)
                    if close_rect.collidepoint(mx, my):
                        # Delete group
                        key = item['key']
                        if key in self.groups:
                            # Clear group attribute on members
                            for c in self.groups[key]:
                                try:
                                    if getattr(c, 'group', None) == key:
                                        setattr(c, 'group', None)
                                except Exception:
                                    pass
                            del self.groups[key]
                        # clear sticky/hover if needed
                        if self.sticky_open_group == key:
                            self.sticky_open_group = None
                        if self.hover_group_key == key:
                            self.hover_group_key = None
                        handled = True
                        break
                    else:
                        # Begin rename if clicking name area
                        name_rect = pygame.Rect(self.rect.x + 8, gy + 4, inner_w - self.close_w - 10, self.line_h)
                        if name_rect.collidepoint(mx, my):
                            self.rename_group_key = item['key']
                            self.rename_box = TextBox(name_rect.copy(), self.font, placeholder="Group Name")
                            self.rename_box.text = item['key']
                            handled = True
                            break
                        # Else group selection behavior
                        if event.button == 1:
                            # Left click: replace or add selection depending on Shift
                            mods = pygame.key.get_mods()
                            if not (mods & pygame.KMOD_SHIFT):
                                self.selected_entities.clear()
                            for c in item['cells']:
                                if c not in self.selected_entities:
                                    self.selected_entities.append(c)
                        elif event.button == 3:
                            # Right click: toggle selection state of entire group
                            all_selected = all(c in self.selected_entities for c in item['cells'])
                            if all_selected:
                                # Deselect all in group
                                self.selected_entities[:] = [c for c in self.selected_entities if c not in item['cells']]
                            else:
                                # Add any missing
                                for c in item['cells']:
                                    if c not in self.selected_entities:
                                        self.selected_entities.append(c)
                        # Make the group sticky-open so we can move into its cells
                        self.hover_group_key = item['key']
                        self.sticky_open_group = item['key']
                        handled = True
                        break
                elif item['type'] == 'cell':
                    # Click on cells within expanded group; keep group open
                    self.hover_group_key = item['group']
                    self.sticky_open_group = item['group']
                    mods = pygame.key.get_mods()
                    cell = item['cell']
                    if event.button == 1:
                        if not (mods & pygame.KMOD_SHIFT):
                            self.selected_entities.clear()
                        if cell in self.selected_entities:
                            self.selected_entities.remove(cell)
                        else:
                            self.selected_entities.append(cell)
                    elif event.button == 3:
                        # Right-click toggles this one cell independent of shift
                        if cell in self.selected_entities:
                            self.selected_entities.remove(cell)
                        else:
                            self.selected_entities.append(cell)
                    handled = True
                    break

        # Handle renaming input
        if self.rename_box:
            action = self.rename_box.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                # Commit or cancel
                new_name = self.rename_box.text.strip()
                old_key = self.rename_group_key
                if event.key == pygame.K_RETURN and new_name and old_key in self.groups:
                    if new_name != old_key and new_name not in self.groups:
                        # rename dict key
                        members = self.groups.pop(old_key)
                        self.groups[new_name] = members
                        # update each member's group attribute
                        for c in members:
                            try:
                                setattr(c, 'group', new_name)
                            except Exception:
                                pass
                        self.rename_group_key = new_name
                # End rename mode
                self.rename_box = None
            handled = handled or (action == "typing")

        return handled

    def draw(self, surface, y_override=None):
        if y_override is not None:
            self.rect.y = y_override
        
        # Create semi-transparent background
        bg_surface = pygame.Surface((self.rect.width, self.rect.height))
        bg_surface.set_alpha(200)  # Slightly transparent
        bg_surface.fill((40, 40, 40))
        surface.blit(bg_surface, self.rect)
        
        pygame.draw.rect(surface, (71, 86, 87), self.rect, 2)
        # Title
        title = self.font.render("Groups", True, SILVER)
        surface.blit(title, (self.rect.x + 8, self.rect.y + 6))

        list_top, list_h = self._visible_area()
        inner_w = self.rect.width - 12
        view_rect = pygame.Rect(self.rect.x + 6, list_top, inner_w, list_h)

        # Compute total height to clamp scroll
        total_h = 0
        it = list(self._iter_layout(inner_w))
        if it and 'total_h' in it[-1]:
            total_h = it[-1]['total_h']
        self.scroll_px = min(self.scroll_px, max(0, total_h - list_h))

        # Draw visible rows only
        clip = surface.get_clip()
        surface.set_clip(view_rect)
        for item in it:
            if 'type' not in item:
                continue
            draw_y = list_top + item['y'] - self.scroll_px
            if draw_y + item['h'] < list_top or draw_y > list_top + list_h:
                continue
            if item['type'] == 'group':
                is_hover = (item['key'] == self.hover_group_key) or (item['key'] == self.sticky_open_group)
                bg_col = LIGHT_BLUE if is_hover else DARK_BLUE
                row_rect = pygame.Rect(self.rect.x + 6, draw_y, inner_w, item['h'] - 2)
                pygame.draw.rect(surface, bg_col, row_rect)
                # name
                text_w = inner_w - self.close_w - 10
                y_cursor = draw_y + 4
                for line in item['lines']:
                    txt = self.font.render(line, True, SILVER)
                    surface.blit(txt, (self.rect.x + 8, y_cursor))
                    y_cursor += self.line_h
                # close 'x'
                x_rect = pygame.Rect(self.rect.x + self.rect.width - self.close_w - 6, draw_y + 4, self.close_w, self.line_h)
                pygame.draw.rect(surface, (100, 60, 60), x_rect)
                x_txt = self.font.render("x", True, (255, 255, 255))
                surface.blit(x_txt, (x_rect.x + (self.close_w - x_txt.get_width()) // 2, x_rect.y))
                # rename textbox overlay if active
                if self.rename_box and self.rename_group_key == item['key']:
                    self.rename_box.draw(surface)
            elif item['type'] == 'cell':
                cell = item['cell']
                row_rect = pygame.Rect(self.rect.x + 10, draw_y, inner_w - 8, item['h'] - 2)
                pygame.draw.rect(surface, (60, 60, 60), row_rect)
                # small color swatch using body_color
                cc = getattr(cell, 'body_color', (180, 255, 180))
                pygame.draw.rect(surface, cc, (row_rect.x + 4, row_rect.y + 4, 12, self.line_h - 6))
                label = getattr(cell, 'name', 'Cell')
                txt = self.font.render(label, True, SILVER)
                surface.blit(txt, (row_rect.x + 22, row_rect.y + 2))
                
                # Draw health percentage on the right side
                health_pct = cell.get_health_percentage() if hasattr(cell, 'get_health_percentage') else 100
                health_color = (0, 255, 0) if health_pct > 60 else (255, 255, 0) if health_pct > 30 else (255, 0, 0)
                health_text = f"{health_pct}%"
                health_surf = self.font.render(health_text, True, health_color)
                health_x = row_rect.right - health_surf.get_width() - 4
                surface.blit(health_surf, (health_x, row_rect.y + 2))
        surface.set_clip(clip)

class UpgradeSectionUI:
    def __init__(self, screen, player, font):
        self.screen = screen
        self.player = player
        self.font = font

    def draw(self, delta_time):
        pass

    def handle_event(self, event):
        pass

class ProteinsSectionUI(UpgradeSectionUI):
    def __init__(self, screen, player, font):
        super().__init__(screen, player, font)
        self.categories = ["Structure", "Enzymes", "Attack", "Defense"]
        self.protein_data = PROTEIN_DATA
        self.selected_category = self.categories[0]
        self.category_buttons = []
        tab_w, tab_h = 120, 32
        padding = 10

        for i, cat in enumerate(self.categories):
            x = 50 + i * (tab_w + padding)
            btn = Button(
                rect=(x, SCREEN_HEIGHT - 320, tab_w, tab_h),
                text=cat,
                callback=lambda c=cat: self.set_category(c),
                font=font
            )
            self.category_buttons.append(btn)
        self.protein_buttons = []
        self.selected_item = None
        self.buy_button = Button((SCREEN_WIDTH - 220, SCREEN_HEIGHT - 120, 160, 50), "Buy", self.buy_selected, font)
        self.rebuild_protein_buttons()

        self.preview_panel = None

    def set_category(self, category):
        self.selected_category = category
        self.selected_item = None
        self.rebuild_protein_buttons()

    def rebuild_protein_buttons(self):
        self.protein_buttons.clear()
        items = self.protein_data[self.selected_category]
        for idx, prot in enumerate(items):
            x = 50
            y = 120 + idx * 40
            cost = prot["cost"]
            cost_str = f"P{cost['protein']} L{cost['lipid']} C{cost['carbohydrate']} N{cost['nucleic_acid']}"
            label = f"{prot['name']} ({cost_str})"
            btn = Button(
                rect=(x, y, 360, 30),
                text=label,
                callback=lambda p=prot: self.select_item(p),
                font=self.font
            )
            self.protein_buttons.append(btn)

    def select_item(self, item):
        self.selected_item = item

    def buy_selected(self):
        if self.selected_item:
            from main import player_molecules, player_upgrades
            # Check if we can afford the item
            cost = self.selected_item['cost']
            if all(player_molecules.get(k, 0) >= v for k, v in cost.items()):
                # Deduct costs from central storage
                for k, v in cost.items():
                    player_molecules[k] -= v
                # Create a proper BuyableProteinUpgrade object
                upgrade = BuyableProteinUpgrade(
                    name=self.selected_item['name'],
                    desc=self.selected_item['desc'],
                    boosts=self.selected_item['boosts'],
                    color=self.selected_item.get('color', (100,180,255)),
                    symbol=self.selected_item.get('symbol', None)
                )
                # Always add to player upgrades to allow stacking
                player_upgrades['Proteins'].append(upgrade)
                print(f"Purchased {upgrade.name} remaining: {player_molecules}")
                
                # Trigger discovery tracking for protein purchase
                from main import discovery_tracker
                if discovery_tracker:
                    discovery_tracker.on_protein_purchased(upgrade.name)

    def draw(self, delta_time):
        preview_x = SCREEN_WIDTH - 260
        preview_y = 120
        preview_w = 240
        panel_rect = (preview_x, preview_y, preview_w, 200)
        icon = None
        content = []
        # Draw category tabs with highlight
        for btn in self.category_buttons:
            btn.draw(self.screen)
            if btn.text == self.selected_category:
                pygame.draw.rect(self.screen, LIGHT_BLUE, btn.rect, 2)

        # Draw protein option buttons, highlight if selected
        for btn, prot in zip(self.protein_buttons, self.protein_data[self.selected_category]):
            btn.draw(self.screen)
            if self.selected_item == prot:
                pygame.draw.rect(self.screen, (255, 255, 0), btn.rect, 3)

        # Build preview panel content
        if self.selected_item:
            preview_icon = BuyableProteinUpgrade(
                name=self.selected_item["name"],
                desc=self.selected_item["desc"],
                boosts=self.selected_item["boosts"],
                color=self.selected_item.get("color", (100,180,255)),
                symbol=self.selected_item.get("symbol", None)
            ).icon
            icon = preview_icon
            content = [
                {"text": self.selected_item["name"], "mode": "static", "color": SILVER},
                {"text": self.selected_item.get("desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = self.selected_item.get("boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        panel = TextPanel(panel_rect, self.font, content, icon=icon)
        panel.draw(self.screen, delta_time)
        self.buy_button.draw(self.screen)

        if self.preview_panel is None:
            self.preview_panel = TextPanel(panel_rect, self.font, content, icon=icon)
        else:
            self.preview_panel.set_content(content)
            self.preview_panel.set_icon(icon)
        self.preview_panel.draw(self.screen, delta_time)
        self.buy_button.draw(self.screen)

    def handle_event(self, event):
        for btn in self.category_buttons:
            btn.handle_event(event)
        for btn in self.protein_buttons:
            btn.handle_event(event)
        preview_x = SCREEN_WIDTH - 260
        preview_y = 120
        preview_w = 240
        panel_rect = (preview_x, preview_y, preview_w, 200)
        icon = None
        content = []
        if self.selected_item:
            preview_icon = BuyableProteinUpgrade(
                name=self.selected_item["name"],
                desc=self.selected_item["desc"],
                boosts=self.selected_item["boosts"],
                color=self.selected_item.get("color", (100,180,255)),
                symbol=self.selected_item.get("symbol", None)
            ).icon
            icon = preview_icon
            content = [
                {"text": self.selected_item["name"], "mode": "static", "color": SILVER},
                {"text": self.selected_item.get("desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = self.selected_item.get("boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        panel = TextPanel(panel_rect, self.font, content, icon=icon)
        panel.handle_event(event)
        if self.preview_panel:
            self.preview_panel.handle_event(event)
        if self.selected_item:
            self.buy_button.handle_event(event)

class OrganellesSectionUI(UpgradeSectionUI):
    def __init__(self, screen, player, font):
        super().__init__(screen, player, font)
        self.categories = ["Universal", "Prokaryotic", "Plant", "Animal"]
        self.organelle_data = ORGANELLE_DATA
        self.selected_category = self.categories[0]
        self.category_buttons = []
        tab_w, tab_h = 120, 32
        padding = 10
        for i, cat in enumerate(self.categories):
            x = 50 + i * (tab_w + padding)
            btn = Button(
                rect=(x, SCREEN_HEIGHT - 280, tab_w, tab_h),
                text=cat,
                callback=lambda c=cat: self.set_category(c),
                font=font
            )
            self.category_buttons.append(btn)
        self.selected_item = None
        self.buy_button = Button((SCREEN_WIDTH - 220, SCREEN_HEIGHT - 120, 160, 50), "Buy", self.buy_selected, font)
        self.organelle_buttons = []
        self.rebuild_organelle_buttons()

        self.preview_panel = None

    def set_category(self, category):
        self.selected_category = category
        self.selected_item = None
        self.rebuild_organelle_buttons()

    def rebuild_organelle_buttons(self):
        self.organelle_buttons.clear()
        items = self.organelle_data[self.selected_category]
        for idx, org in enumerate(items):
            x = 50
            y = 120 + idx * 40
            cost = org["cost"]
            cost_str = f"P{cost['protein']} L{cost['lipid']} C{cost['carbohydrate']} N{cost['nucleic_acid']}"
            label = f"{org['name']} ({cost_str})"
            btn = Button(
                rect=(x, y, 360, 30),
                text=label,
                callback=lambda o=org: self.select_item(o),
                font=self.font
            )
            self.organelle_buttons.append(btn)

    def buy_selected(self):
        if self.selected_item:
            from main import player_molecules, player_upgrades
            # Check if we can afford the item
            cost = self.selected_item['cost']
            if all(player_molecules.get(k, 0) >= v for k, v in cost.items()):
                # Deduct costs from central storage
                for k, v in cost.items():
                    player_molecules[k] -= v
                # Create a proper OrganelleUpgrade object
                upgrade = OrganelleUpgrade(
                    name=self.selected_item['name'],
                    desc=self.selected_item['desc'],
                    boosts=self.selected_item['boosts'],
                    color=self.selected_item.get('color', (100,180,255)),
                    symbol=self.selected_item.get('symbol', None)
                )
                # Always add to organelles to allow stacking
                player_upgrades['Organelles'].append(upgrade)
                print(f"Purchased {upgrade.name} remaining: {player_molecules}")
                
                # Trigger discovery tracking for organelle purchase
                from main import discovery_tracker
                if discovery_tracker:
                    discovery_tracker.on_organelle_purchased(upgrade.name)

    def select_item(self, item):
        self.selected_item = item

    def draw(self, delta_time):
        preview_x = SCREEN_WIDTH - 260
        preview_y = 120
        preview_w = 240
        panel_rect = (preview_x, preview_y, preview_w, 200)
        icon = None
        content = []
        # ...category and organelle button drawing...
        if self.selected_item:
            preview_icon = OrganelleUpgrade(
                name=self.selected_item["name"],
                desc=self.selected_item["desc"],
                boosts=self.selected_item["boosts"],
                color=self.selected_item.get("color", (100,180,255)),
                symbol=self.selected_item.get("symbol", None)
            ).icon
            icon = preview_icon
            content = [
                {"text": self.selected_item["name"], "mode": "static", "color": SILVER},
                {"text": self.selected_item.get("desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = self.selected_item.get("boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        if self.preview_panel is None:
            self.preview_panel = TextPanel(panel_rect, self.font, content, icon=icon)
        else:
            self.preview_panel.set_content(content)
            self.preview_panel.set_icon(icon)

        # Draw category tabs with highlight
        for btn in self.category_buttons:
            btn.draw(self.screen)
            if btn.text == self.selected_category:
                pygame.draw.rect(self.screen, LIGHT_BLUE, btn.rect, 2)

        # Draw organelle option buttons, highlight if selected
        for btn, org in zip(self.organelle_buttons, self.organelle_data[self.selected_category]):
            btn.draw(self.screen)
            if self.selected_item == org:
                pygame.draw.rect(self.screen, (255, 255, 0), btn.rect, 3)

        self.preview_panel.draw(self.screen, delta_time)
        self.buy_button.draw(self.screen)

    def handle_event(self, event):
        for btn in self.category_buttons:
            btn.handle_event(event)
        for btn in self.organelle_buttons:
            btn.handle_event(event)
        preview_x = SCREEN_WIDTH - 260
        preview_y = 120
        preview_w = 240
        panel_rect = (preview_x, preview_y, preview_w, 200)
        icon = None
        content = []
        if self.selected_item:
            preview_icon = OrganelleUpgrade(
                name=self.selected_item["name"],
                desc=self.selected_item["desc"],
                boosts=self.selected_item["boosts"],
                color=self.selected_item.get("color", (100,180,255)),
                symbol=self.selected_item.get("symbol", None)
            ).icon
            icon = preview_icon
            content = [
                {"text": self.selected_item["name"], "mode": "static", "color": SILVER},
                {"text": self.selected_item.get("desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = self.selected_item.get("boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        panel = TextPanel(panel_rect, self.font, content, icon=icon)
        panel.handle_event(event)
        if self.preview_panel:
            self.preview_panel.handle_event(event)
        if self.selected_item:
            self.buy_button.handle_event(event)

class InventorySectionUI(UpgradeSectionUI):
    
    def __init__(self, screen, player, font, selected_entities=None):
        super().__init__(screen, player, font)
        self.scroll_offset = 0
        self.scroll_speed = 30
        self.inventory_rect = pygame.Rect(20, SCREEN_HEIGHT - 200, 470, 180)
        self.active_filter = "All"
        self.buttons = [
            Button((20, SCREEN_HEIGHT - 240, 110, 30), "All", lambda: self.set_filter("All"), font),
            Button((140, SCREEN_HEIGHT - 240, 110, 30), "Proteins", lambda: self.set_filter("Proteins"), font),
            Button((260, SCREEN_HEIGHT - 240, 110, 30), "Organelles", lambda: self.set_filter("Organelles"), font),
            Button((380, SCREEN_HEIGHT - 240, 110, 30), "Crafted Proteins", lambda: self.set_filter("Crafted Proteins"), font)
        ]
        tb_rect = pygame.Rect(20, SCREEN_HEIGHT - 280, 470, 30)
        self.search_box = TextBox(tb_rect, font, placeholder="Search…")
        self.selected_item = None
        self.selected_index = None
        self.selected_from_equipped = False
        self.selected_from_organelle_panel = False

        self.equip_button = Button(
            rect=pygame.Rect(850, 675, 85, 40),
            text="Equip",
            callback=self.equip_selected,
            font=font
        )
        self.unequip_button = Button(
            rect=pygame.Rect(850, 675, 85, 40),
            text="Unequip",
            callback=self.unequip_selected,
            font=font
        )

        # Equipped panel
        panel_w, panel_h = 330, 340
        panel_x = 160
        panel_y = 120
        self.equipped_panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        self.equip_search = TextBox(pygame.Rect(panel_x, panel_y - 40, panel_w, 30), font, placeholder="Search equipped…")
        self.equip_scroll = 0
        self.equip_speed = 30
        self.name_scroll_offset = 0.0
        self.name_scroll_speed = 45

        # Organelle slots
        self.organelle_slot_rects = []
        slot_w, slot_h = 60, 60
        start_x, start_y = 20, 120
        padding = 10
        for i in range(5):
            y = start_y + i * (slot_h + padding)
            self.organelle_slot_rects.append(pygame.Rect(start_x, y, slot_w, slot_h))
        start_x, start_y = 90, 120
        for i in range(5):
            y = start_y + i * (slot_h + padding)
            self.organelle_slot_rects.append(pygame.Rect(start_x, y, slot_w, slot_h))

        self.desc_panel = None

        # --- Entity preview state ---
        self.selected_entities = selected_entities if selected_entities is not None else []
        self.entity_preview_index = 0



    def set_filter(self, category):
        self.active_filter = category
        self.scroll_offset = 0
        self.selected_item = None
        self.selected_index = None
        self.selected_from_equipped = False
        self.selected_from_organelle_panel = False

    def get_grouped_inventory(self):
        # Returns a dict: (name, category) -> [item, count]
        from main import player_upgrades
        grouped = {}
        for category, upgrade_list in player_upgrades.items():
            for item in upgrade_list:
                # Handle both proper Upgrade objects and raw dictionaries
                name = item.name if hasattr(item, 'name') else item.get('name', 'Unknown')
                item_category = category  # Use the dictionary key as category
                
                # Convert raw dictionaries to proper Upgrade objects if needed
                if isinstance(item, dict):
                    if category in ['Proteins', 'Crafted Proteins']:
                        item = BuyableProteinUpgrade(
                            name=item['name'],
                            desc=item.get('desc', ''),
                            boosts=item.get('boosts', []),
                            color=item.get('color', (100,180,255)),
                            symbol=item.get('symbol', None)
                        )
                    else:  # Organelles
                        item = OrganelleUpgrade(
                            name=item['name'],
                            desc=item.get('desc', ''),
                            boosts=item.get('boosts', []),
                            color=item.get('color', (100,180,255)),
                            symbol=item.get('symbol', None)
                        )
                
                key = (name, item_category)
                if key not in grouped:
                    grouped[key] = [item, 1]
                else:
                    grouped[key][1] += 1
        return grouped

    def get_filtered_items(self):
        query = self.search_box.text.lower()
        grouped = self.get_grouped_inventory()
        items = []
        for (name, category), (item, count) in grouped.items():
            if query in name.lower():
                if self.active_filter == "All" or category == self.active_filter:
                    items.append((item, count))
        # NEW: sort by name for a stable grid order
        items.sort(key=lambda it: it[0].name)
        return items
    
    def get_item_count(self, item):
        grouped = self.get_grouped_inventory()
        return grouped.get((item.name, item.category), [item, 0])[1]

    def equip_selected(self):
        if self.selected_index is None:
            return
        
        # Get the currently selected entity
        current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
        
        # Only allow equipping for player cells
        if not current_entity or not hasattr(current_entity, 'is_player') or not current_entity.is_player:
            return
            
        items = self.get_filtered_items()
        # re‑fetch based on index
        item, count = items[self.selected_index]

        if item.category in ("Proteins", "Crafted Proteins"):
            # Only call equip_protein, let it handle inventory logic
            if current_entity.equip_protein(item):
                # if no more left, clear selection
                if self.get_item_count(item) == 0:
                    self.selected_index = None

        elif item.category == "Organelles":
            # early-out if no free slot
            if all(slot is not None for slot in current_entity.organelle_slots):
                return

            # place in first empty slot
            for idx, slot in enumerate(current_entity.organelle_slots):
                if slot is None:
                    current_entity.equip_organelle(idx, item)
                    break
            if self.get_item_count(item) == 0:
                self.selected_index = None
                

    def unequip_selected(self):
        if not self.selected_item:
            return
            
        # Get the currently selected entity
        current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
        
        # Only allow unequipping for player cells
        if not current_entity or not hasattr(current_entity, 'is_player') or not current_entity.is_player:
            return
            
        item = self.selected_item
        from main import player_upgrades
        if self.selected_from_equipped:
            if item in current_entity.protein_inventory:
                # Use proper unequip method to handle visual cleanup
                if current_entity.unequip_protein(item):
                    # Keep selected if still equipped, else clear
                    if item in current_entity.protein_inventory:
                        self.selected_item = item
                    else:
                        self.selected_item = None
        elif self.selected_from_organelle_panel:
            for idx, slot in enumerate(current_entity.organelle_slots):
                if slot == item:
                    current_entity.organelle_slots[idx] = None
                    player_upgrades["Organelles"].append(item)
                    break
            # Keep selected if still equipped, else clear
            if item in current_entity.organelle_slots:
                self.selected_item = item
            else:
                self.selected_item = None

    def handle_event(self, event):
        from main import selected_entities
        self.selected_entities = selected_entities
        # Handle left/right arrow for entity preview cycling
        if self.selected_entities:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.entity_preview_index = (self.entity_preview_index - 1) % len(self.selected_entities)
                elif event.key == pygame.K_RIGHT:
                    self.entity_preview_index = (self.entity_preview_index + 1) % len(self.selected_entities)

        for btn in self.buttons:
            btn.handle_event(event)
        prev_inv = self.search_box.text
        self.search_box.handle_event(event)
        if self.search_box.text != prev_inv:
            self.scroll_offset = 0

        prev_equip = self.equip_search.text
        self.equip_search.handle_event(event)
        if self.equip_search.text != prev_equip:
            self.equip_scroll = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in (4, 5):
                if self.equipped_panel.collidepoint(event.pos):
                    if event.button == 4:
                        self.equip_scroll = min(self.equip_scroll + self.equip_speed, 0)
                    else:
                        current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
                        count = len(current_entity.protein_inventory) if current_entity and hasattr(current_entity, 'protein_inventory') else 0
                        total_h = count * (self.font.get_height() + 8)
                        min_scroll = min(0, self.equipped_panel.height - total_h - 5)
                        self.equip_scroll = max(self.equip_scroll - self.equip_speed, min_scroll)
                elif self.inventory_rect.collidepoint(event.pos):
                    if event.button == 4:
                        self.scroll_offset -= self.scroll_speed
                    else:
                        self.scroll_offset = min(self.scroll_offset + self.scroll_speed, 0)
            elif event.button == 1:
                shift_held = pygame.key.get_mods() & pygame.KMOD_SHIFT
                # Select from equipped proteins
                if self.equipped_panel.collidepoint(event.pos):
                    rel_y = event.pos[1] - self.equipped_panel.y - self.equip_scroll - 5
                    idx = rel_y // (self.font.get_height() + 8)
                    query = self.equip_search.text.lower()
                    current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
                    equipped = [p for p in current_entity.protein_inventory if query in p.name.lower()] if current_entity and hasattr(current_entity, 'protein_inventory') else []
                    if 0 <= idx < len(equipped):
                        self.selected_item = equipped[idx]
                        self.selected_from_equipped = True
                        self.selected_from_organelle_panel = False
                        self.name_scroll_offset = 0
                        if shift_held:
                            self.unequip_selected()
                        return
                # Select from organelle panel
                elif any(slot_rect.collidepoint(event.pos) for slot_rect in self.organelle_slot_rects):
                    for idx, slot_rect in enumerate(self.organelle_slot_rects):
                        if slot_rect.collidepoint(event.pos):
                            current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
                            equipped = current_entity.organelle_slots[idx] if current_entity and hasattr(current_entity, 'organelle_slots') else None
                            if equipped:
                                self.selected_item = equipped
                                self.selected_from_organelle_panel = True
                                self.selected_from_equipped = False
                                self.name_scroll_offset = 0
                                if shift_held:
                                    self.unequip_selected()
                                return
                # Select from inventory
                elif self.inventory_rect.collidepoint(event.pos):
                    items = self.get_filtered_items()
                    start_x = self.inventory_rect.x + 15
                    start_y = self.inventory_rect.y + self.scroll_offset + 10
                    cols = 5
                    cell_w, cell_h = 90, 70
                    for idx, (item, count) in enumerate(items):
                        row = idx // cols
                        col = idx % cols
                        cell_rect = pygame.Rect(
                            start_x + col * cell_w,
                            start_y + row * cell_h,
                            80, 60
                        )
                        if cell_rect.collidepoint(event.pos):
                            # set selected index, not object
                            self.selected_index = idx
                            self.selected_item = item
                            self.selected_from_equipped = False
                            self.selected_from_organelle_panel = False
                            self.name_scroll_offset = 0
                            # optionally auto‑equip on shift
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                self.equip_selected()
                            return

        # Description panel event handling
        panel_x = SCREEN_WIDTH - 500
        panel_y = SCREEN_HEIGHT - 280
        panel_w = 480
        panel_h = 260
        panel_rect = (panel_x, panel_y, panel_w, panel_h)
        icon = getattr(self.selected_item, "icon", None) if self.selected_item else None
        content = []
        if self.selected_item:
            name_surface = self.font.render(self.selected_item.name, True, SILVER)
            name_width = name_surface.get_width()
            max_name_width = panel_w - 20
            content = [
                {"text": self.selected_item.name, "mode": "scrolling" if name_width > max_name_width else "static", "color": SILVER},
                {"text": getattr(self.selected_item, "desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = self.selected_item.boosts
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        panel = TextPanel(panel_rect, self.font, content, icon=icon)
        panel.handle_event(event)

        if self.desc_panel:
            self.desc_panel.handle_event(event)

        # Equip/Unequip buttons
        if self.selected_item:
            if self.selected_from_equipped or self.selected_from_organelle_panel:
                self.unequip_button.handle_event(event)
            else:
                self.equip_button.handle_event(event)



    def draw(self, delta_time):
        panel_x = SCREEN_WIDTH - 500
        panel_y = SCREEN_HEIGHT - 280
        panel_w = 480
        panel_h = 260
        panel_rect = (panel_x, panel_y, panel_w, panel_h)

        icon = getattr(self.selected_item, "icon", None) if self.selected_item else None
        content = []

        # --- Entity preview (draw actual entity) ---
        self.preview_center = pygame.Vector2(750, 200)
        self.preview_radius = 60
        preview_rect = pygame.Rect(self.preview_center.x - self.preview_radius, self.preview_center.y - self.preview_radius, self.preview_radius*2, self.preview_radius*2)
        if self.selected_entities and len(self.selected_entities) > 0:
            entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)]
            # Draw a white background circle for clarity
            pygame.draw.circle(self.screen, (220, 220, 255), self.preview_center, self.preview_radius)
            # Draw the entity as it appears in-game, centered in the preview
             # --- FIX: Create a dummy camera for the preview ---
            class PreviewCamera:
                def __init__(self, pos, zoom=1.0):
                    self.pos = pygame.Vector2(pos)
                    self.zoom = zoom
                def world_to_screen(self, world_pos):
                    # Convert world coordinates to screen coordinates
                    return (world_pos - self.pos) * self.zoom + pygame.Vector2(self.preview_radius, self.preview_radius)
                def apply_zoom(self, surface):
                    # Scale based on preview zoom
                    size = surface.get_size()
                    scaled_size = (int(size[0] * self.zoom), int(size[1] * self.zoom))
                    if scaled_size[0] > 0 and scaled_size[1] > 0:
                        return pygame.transform.smoothscale(surface, scaled_size)
                    return surface

            # Determine the right zoom level to make the entity fit
            # Calculate appropriate zoom level
            entity_radius = getattr(entity, 'radius', self.preview_radius)
            preview_zoom = (self.preview_radius / entity_radius) * 0.8  # 80% of preview area
            
            # Create preview surface and camera
            preview_size = self.preview_radius * 2
            surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
            preview_camera = PreviewCamera(pygame.Vector2(preview_size/2, preview_size/2), zoom=preview_zoom)
            
            try:
                # Save original position
                old_pos = None
                if hasattr(entity, 'pos'):
                    old_pos = entity.pos.copy()
                    entity.pos = pygame.Vector2(preview_size/2, preview_size/2)
                
                # Draw the entity
                entity.draw(surf, preview_camera)
                
                # Restore original position
                if old_pos is not None:
                    entity.pos = old_pos
                self.screen.blit(surf, preview_rect.topleft)
                print("runnin this")
            except Exception:
                # Fallback: draw a colored circle with entity type name
                pygame.draw.circle(self.screen, (100, 200, 255), self.preview_center, self.preview_radius)
                etype = type(entity).__name__
                txt = self.font.render(etype, True, (0,0,0))
                txt_rect = txt.get_rect(center=self.preview_center)
                self.screen.blit(txt, txt_rect)
            # Draw entity name below
            etype = type(entity).__name__
            name = getattr(entity, 'name', etype)
            name_surf = self.font.render(name, True, (80, 180, 255))
            name_rect = name_surf.get_rect(center=(self.preview_center.x, self.preview_center.y + self.preview_radius + 18))
            self.screen.blit(name_surf, name_rect)
            # Draw left/right arrows if >1 entity
            if len(self.selected_entities) > 1:
                arrow_color = (80, 180, 255)
                pygame.draw.polygon(self.screen, arrow_color, [
                    (self.preview_center.x - self.preview_radius - 18, self.preview_center.y),
                    (self.preview_center.x - self.preview_radius - 2, self.preview_center.y - 12),
                    (self.preview_center.x - self.preview_radius - 2, self.preview_center.y + 12)
                ])
                pygame.draw.polygon(self.screen, arrow_color, [
                    (self.preview_center.x + self.preview_radius + 18, self.preview_center.y),
                    (self.preview_center.x + self.preview_radius + 2, self.preview_center.y - 12),
                    (self.preview_center.x + self.preview_radius + 2, self.preview_center.y + 12)
                ])
            
            # Draw attributes panel next to preview
            if hasattr(entity, 'attributes'):
                attr_x = self.preview_center.x + self.preview_radius + 30
                attr_y = self.preview_center.y - self.preview_radius
                attr_panel = pygame.Rect(attr_x, attr_y, 150, self.preview_radius * 2)
                
                # Draw panel background
                pygame.draw.rect(self.screen, (40, 40, 40), attr_panel)
                pygame.draw.rect(self.screen, GRAY, attr_panel, 2)
                
                # Draw attributes
                text_y = attr_y + 10
                line_height = self.font.get_height() + 5
                for attr, value in entity.attributes.items():
                    text = f"{attr}: {value}"
                    text_surf = self.font.render(text, True, SILVER)
                    self.screen.blit(text_surf, (attr_x + 10, text_y))
                    text_y += line_height
            # --- Entity info panel (below preview) ---
            info_y = self.preview_center.y + self.preview_radius + 40
            info_lines = []
            # Show only relevant info for entity type
            if hasattr(entity, 'health'):
                info_lines.append(f"Health: {getattr(entity, 'health', '?')}")
            if hasattr(entity, 'energy'):
                info_lines.append(f"Energy: {getattr(entity, 'energy', '?')}")
            if hasattr(entity, 'proteins') and getattr(entity, 'proteins', None):
                info_lines.append(f"Proteins: {len(entity.proteins)}")
            if hasattr(entity, 'organelles') and getattr(entity, 'organelles', None):
                info_lines.append(f"Organelles: {len(entity.organelles)}")
            # For viruses, show unique info if available
            if hasattr(entity, 'virus_type'):
                info_lines.append(f"Type: {getattr(entity, 'virus_type', '?')}")
            # Draw info lines
            for i, line in enumerate(info_lines):
                info_surf = self.font.render(line, True, (180, 220, 255))
                info_rect = info_surf.get_rect(center=(self.preview_center.x, info_y + i*22))
                self.screen.blit(info_surf, info_rect)
        else:
            # Fallback: draw the original cyan circle if no entity selected
            pygame.draw.circle(self.screen, (100, 200, 255), self.preview_center, self.preview_radius)

        # Equipped proteins panel
        pygame.draw.rect(self.screen, (40, 40, 40), self.equipped_panel)
        pygame.draw.rect(self.screen, GRAY, self.equipped_panel, 2)
        self.equip_search.update(delta_time)
        self.equip_search.draw(self.screen)
        clip = self.screen.get_clip()
        self.screen.set_clip(self.equipped_panel)
        query = self.equip_search.text.lower()
        
        # Get the proteins of the currently previewed entity
        current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
        if current_entity and hasattr(current_entity, 'protein_inventory'):
            equipped = [p for p in current_entity.protein_inventory if query in p.name.lower()]
            y = self.equipped_panel.y + self.equip_scroll + 5
            for prot in equipped:
                txt = self.font.render(prot.name, True, SILVER)
                rect = txt.get_rect(topleft=(self.equipped_panel.x + 5, y))
                self.screen.blit(txt, rect)
                if self.selected_from_equipped and self.selected_item == prot:
                    pygame.draw.rect(self.screen, LIGHT_BLUE, rect, 2)
                y += self.font.get_height() + 8
        self.screen.set_clip(clip)

        # Organelles slots
        for idx, slot_rect in enumerate(self.organelle_slot_rects):
            pygame.draw.rect(self.screen, (50,50,50), slot_rect)
            pygame.draw.rect(self.screen, GRAY, slot_rect, 2)
            current_entity = self.selected_entities[self.entity_preview_index % len(self.selected_entities)] if self.selected_entities else None
            if current_entity and hasattr(current_entity, 'organelle_slots'):
                equipped = current_entity.organelle_slots[idx]
                if equipped:
                    equipped.draw_icon(self.screen, (slot_rect.x + 10, slot_rect.y + 10))
                    if self.selected_from_organelle_panel and self.selected_item == equipped:
                        pygame.draw.rect(self.screen, LIGHT_BLUE, slot_rect, 3)

        # Search bar
        self.search_box.update(delta_time)
        self.search_box.draw(self.screen)

        # Filter buttons
        for button in self.buttons:
            button.draw(self.screen)
            if button.text == self.active_filter:
                pygame.draw.rect(self.screen, LIGHT_BLUE, button.rect, 2)

        # Inventory panel
        pygame.draw.rect(self.screen, (30, 30, 30), self.inventory_rect)
        pygame.draw.rect(self.screen, GRAY, self.inventory_rect, 2)
        self.screen.set_clip(self.inventory_rect)

        items = self.get_filtered_items()
        start_x = self.inventory_rect.x + 15
        start_y = self.inventory_rect.y + self.scroll_offset + 10
        cols = 5
        rows = math.ceil(len(items) / cols)

        for i in range(rows):
            y = start_y + i * 70
            for j in range(cols):
                index = i * cols + j
                if index < len(items):
                    item, count = items[index]
                    item_rect = pygame.Rect(start_x + j * 90, y, 80, 60)
                    # draw background & icon
                    item_surf = pygame.Surface((80, 60), pygame.SRCALPHA)
                    item_surf.fill(BROWN)
                    pygame.draw.rect(item_surf, GRAY, item_surf.get_rect(), 2)
                    item.draw_icon(item_surf, (20, 8))

                    # HIGHLIGHT by selected_index
                    if self.selected_index == index and not (self.selected_from_equipped or self.selected_from_organelle_panel):
                        # highlight the grid cell
                        pygame.draw.rect(item_surf, LIGHT_BLUE, item_surf.get_rect(), 3)

                    # draw name (scrolling or static) exactly as before…
                    font_y = 40
                    if self.selected_index == index and not (self.selected_from_equipped or self.selected_from_organelle_panel):
                        # scrolling name logic
                        text_surface = self.font.render(item.name, True, SILVER)
                        text_width   = text_surface.get_width()
                        visible_w    = item_rect.width - 10
                        if text_width > visible_w:
                            self.name_scroll_offset += self.name_scroll_speed * delta_time
                            scroll_dist = self.name_scroll_offset % (text_width + 50)
                            base_x = 5 - scroll_dist
                            item_surf.blit(text_surface, (base_x, font_y))
                            item_surf.blit(text_surface, (base_x + text_width + 50, font_y))
                        else:
                            item_surf.blit(text_surface, (5, font_y))
                    else:
                        # static truncated name
                        static = self.font.render(item.name[:10], True, SILVER)
                        item_surf.blit(static, (5, font_y))

                    # draw stack count badge
                    if count > 1:
                        badge = self.font.render(f"x{count}", True, LIGHT_BLUE)
                        bw, bh = badge.get_size()
                        # right‑align with 5px padding inside the 80px cell
                        bx = item_surf.get_width() - bw - 5  
                        by = 5
                        item_surf.blit(badge, (bx, by))
                    # finally blit the whole cell
                    self.screen.blit(item_surf, item_rect.topleft)
        self.screen.set_clip(None)

        # Description panel for selected item (if still in inventory or equipped)
        show_panel = False
        stack_count = 0
        if self.selected_item:
            if self.selected_from_equipped:
                show_panel = self.selected_item in self.player.protein_inventory
            elif self.selected_from_organelle_panel:
                show_panel = self.selected_item in self.player.organelle_slots
            else:
                stack_count = self.get_item_count(self.selected_item)
                show_panel = stack_count > 0

            if self.desc_panel is None:
                self.desc_panel = TextPanel(panel_rect, self.font, content, icon=icon)
            else:
                self.desc_panel.set_content(content)
                self.desc_panel.set_icon(icon)
            self.desc_panel.draw(self.screen, delta_time)
        

        if show_panel:
            show_panel = False
            stack_count = 0
            if self.selected_item:
                if self.selected_from_equipped:
                    show_panel = self.selected_item in self.player.protein_inventory
                elif self.selected_from_organelle_panel:
                    show_panel = self.selected_item in self.player.organelle_slots
                else:
                    stack_count = self.get_item_count(self.selected_item)
                    show_panel = stack_count > 0
                if show_panel:
                    name_surface = self.font.render(self.selected_item.name, True, SILVER)
                    name_width = name_surface.get_width()
                    max_name_width = panel_w - 20
                    content = [
                        {"text": self.selected_item.name, "mode": "scrolling" if name_width > max_name_width else "static", "color": SILVER},
                        {"text": getattr(self.selected_item, "desc", ""), "mode": "static", "color": SILVER},
                    ]
                    boosts = self.selected_item.boosts
                    if boosts:
                        content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                        for boost in boosts:
                            boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                            content.append({"text": boost_str, "mode": "static", "color": SILVER})
            # Always draw the panel, even if content is empty
            panel = TextPanel(panel_rect, self.font, content, icon=icon)
            panel.draw(self.screen, delta_time)
            # Equip/Unequip buttons only if something is selected and present
            if show_panel:
                if self.selected_from_equipped or self.selected_from_organelle_panel:
                    self.unequip_button.draw(self.screen)
                else:
                    self.equip_button.draw(self.screen)


class ProteinCraftingUI(UpgradeSectionUI):
    def __init__(self, screen, player, font):
        super().__init__(screen, player, font)
        self.seq_box = TextBox(rect=pygame.Rect(60, 120, 300, 40), font=font, placeholder="Enter sequence...", filter=["a", "t", "g", "c"], upper=True)
        self.crafted_protein = None
        self.craft_button = Button((380, 120, 100, 40), "Craft", self.craft_protein, font)
        self.preview_protein = None
        self.selected_codon = None
        self.codon_scroll = 0
        self.codon_scroll_speed = 30
        self.codon_name_scroll_offset = 0.0
        self.codon_name_scroll_speed = 45  # px/sec

        self.codon_panel = None
        self.preview_panel = None

    def draw(self, delta_time):
        self.seq_box.update(delta_time)
        self.seq_box.draw(self.screen)
        self.craft_button.draw(self.screen)

        # --- Codon Discovery Menu ---
        codon_panel_x = 60
        codon_panel_y = 180
        codon_panel_w = 420
        codon_panel_h = 220
        pygame.draw.rect(self.screen, (40, 40, 40), (codon_panel_x, codon_panel_y, codon_panel_w, codon_panel_h))
        pygame.draw.rect(self.screen, GRAY, (codon_panel_x, codon_panel_y, codon_panel_w, codon_panel_h), 2)

        from config import TYPE_CODON_MAP, AMINO_ACID_BOOST_TYPE
        all_codons = sorted(TYPE_CODON_MAP.keys())
        if not hasattr(self.player, "discovered_codons"):
            self.player.discovered_codons = set()
        discovered = self.player.discovered_codons

        # Sort: discovered codons first, then undiscovered, both in original order
        discovered_codons = [c for c in all_codons if c in discovered]
        undiscovered_codons = [c for c in all_codons if c not in discovered]
        codons = discovered_codons + undiscovered_codons

        line_height = self.font.get_height() + 6
        visible_lines = codon_panel_h // line_height
        scroll_offset = self.codon_scroll

        # Draw codon list with horizontal scrolling for long text
        for i, codon in enumerate(codons):
            y = codon_panel_y + 8 + (i * line_height) + scroll_offset
            if codon_panel_y <= y <= codon_panel_y + codon_panel_h - line_height:
                rect = pygame.Rect(codon_panel_x + 8, y, codon_panel_w - 16, line_height)
                highlight = codon == self.selected_codon
                if highlight:
                    pygame.draw.rect(self.screen, LIGHT_BLUE, rect, 2)
                if codon in discovered:
                    info = TYPE_CODON_MAP[codon]
                    acid_type = info["type"]
                    acid_name = next((k for k, v in AMINO_ACID_BOOST_TYPE.items() if v["type"] == acid_type), acid_type)
                    text = f"{codon} - {acid_name}: {acid_type}"
                else:
                    text = "???"
                txt_surf = self.font.render(text, True, SILVER)
                text_w = txt_surf.get_width()
                max_w = rect.width - 8

                # If text is too wide, scroll horizontally for selected codon only
                if text_w > max_w and highlight:
                    self.codon_name_scroll_offset += self.codon_name_scroll_speed * delta_time
                    scroll_dist = self.codon_name_scroll_offset % (text_w + 50)
                    base_x = rect.x + 4 - scroll_dist
                    self.screen.blit(txt_surf, (base_x, rect.y + 2))
                    self.screen.blit(txt_surf, (base_x + text_w + 50, rect.y + 2))
                else:
                    self.screen.blit(txt_surf, (rect.x + 4, rect.y + 2))
                    # Reset scroll offset if not selected
                    if not highlight:
                        self.codon_name_scroll_offset = 0.0

        # --- Preview Panel (right side) ---
        sequence = self.seq_box.text.strip().upper()
        preview = None
        if sequence:
            try:
                preview = CraftedProteinUpgrade(
                    sequence,
                    generate_protein_desc(sequence, TYPE_CODON_MAP),
                    generate_protein_boosts(sequence, TYPE_CODON_MAP),
                    generate_protein_name(sequence, TYPE_CODON_MAP)
                )
            except Exception:
                preview = None
        self.preview_protein = preview

        # --- Description Panel for selected codon ---
        if self.selected_codon and self.selected_codon in discovered:
            panel_x = SCREEN_WIDTH - 450
            panel_y = 120
            panel_w = 430
            panel_h = 220
            panel_rect = (panel_x, panel_y, panel_w, panel_h)
            icon = None
            content = []
            pygame.draw.rect(self.screen, (40, 40, 40), (panel_x, panel_y, panel_w, panel_h))
            pygame.draw.rect(self.screen, GRAY, (panel_x, panel_y, panel_w, panel_h), 2)
            info = TYPE_CODON_MAP[self.selected_codon]
            acid_type = info["type"]
            acid_name = next((k for k, v in AMINO_ACID_BOOST_TYPE.items() if v["type"] == acid_type), acid_type)
            boost_desc = AMINO_ACID_BOOST_TYPE.get(acid_name, {}).get("boost_desc", "")
            acid_desc = AMINO_ACID_BOOST_TYPE.get(acid_name, {}).get("acid_desc", "")
            # Basic info (title) - wrap if too long
            content = []
            title = f"{self.selected_codon} - {acid_name}: {acid_type}; {boost_desc}"
            content.append({"text": title, "mode": "static", "color": SILVER})
            content.append({"text": acid_desc, "mode": "static", "color": SILVER})
            panel_rect = (panel_x, panel_y, panel_w, panel_h)
            panel = TextPanel(panel_rect, self.font, content)
            panel.draw(self.screen, delta_time)

            if self.codon_panel is None:
                self.codon_panel = TextPanel(panel_rect, self.font, content, icon=icon)
            else:
                self.codon_panel.set_content(content)
                self.codon_panel.set_icon(icon)
            self.codon_panel.draw(self.screen, delta_time)


        # --- Live Preview Panel for crafted protein ---
        if self.preview_protein:
            panel_x = SCREEN_WIDTH - 450
            panel_y = 360
            panel_w = 430
            panel_h = 340
            panel_rect = (panel_x, panel_y, panel_w, panel_h)  # <-- define here!
            icon = getattr(self.preview_protein, "icon", None)
            
            # Calculate costs for preview
            sequence = self.seq_box.text.strip().upper()
            required_protein = len(sequence) * 10
            required_nucleic_acid = len(sequence)
            
            content = [
                {"text": getattr(self.preview_protein, "name", ""), "mode": "static", "color": SILVER},
                {"text": getattr(self.preview_protein, "desc", ""), "mode": "static", "color": SILVER},
                {"text": f"Cost: {required_protein} Protein, {required_nucleic_acid} Nucleic Acid", "mode": "static", "color": (255, 200, 100)},
            ]
            boosts = getattr(self.preview_protein, "boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
            panel = TextPanel(panel_rect, self.font, content, icon=icon)
            panel.draw(self.screen, delta_time)

            if self.preview_panel is None:
                self.preview_panel = TextPanel(panel_rect, self.font, content, icon=icon)
            else:
                self.preview_panel.set_content(content)
                self.preview_panel.set_icon(icon)
            self.preview_panel.draw(self.screen, delta_time)

        # Show result after crafting
        y = 180
        #if self.crafted_protein:
            #result_text = self.font.render(f"Crafted: {self.crafted_protein.name}", True, LIGHT_BLUE)
            #self.screen.blit(result_text, (60, y))

    def handle_event(self, event):
        self.seq_box.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.seq_box.focused:
                self.craft_protein()
        if self.codon_panel:
            self.codon_panel.handle_event(event)
        if self.preview_panel:
            self.preview_panel.handle_event(event)
            self.craft_button.handle_event(event)

        # Codon description panel
        panel_x = SCREEN_WIDTH - 450
        panel_y = 120
        panel_w = 430
        panel_h = 220
        content = []
        icon = None
        if self.selected_codon and self.selected_codon in self.player.discovered_codons:
            from config import TYPE_CODON_MAP
            info = TYPE_CODON_MAP[self.selected_codon]
            acid_type = info["type"]
            acid_name = next((k for k, v in AMINO_ACID_BOOST_TYPE.items() if v["type"] == acid_type), acid_type)
            boost_desc = AMINO_ACID_BOOST_TYPE.get(acid_name, {}).get("boost_desc", "")
            acid_desc = AMINO_ACID_BOOST_TYPE.get(acid_name, {}).get("acid_desc", "")
            title = f"{self.selected_codon} - {acid_name}: {acid_type}; {boost_desc}"
            content.append({"text": title, "mode": "static", "color": SILVER})
            content.append({"text": acid_desc, "mode": "static", "color": SILVER})
        codon_panel = TextPanel((panel_x, panel_y, panel_w, panel_h), self.font, content, icon=icon)
        codon_panel.handle_event(event)

        # Preview panel
        panel_x = SCREEN_WIDTH - 450
        panel_y = 360
        panel_w = 430
        panel_h = 340
        icon = getattr(self.preview_protein, "icon", None) if self.preview_protein else None
        content = []
        if self.preview_protein:
            content = [
                {"text": getattr(self.preview_protein, "name", ""), "mode": "static", "color": SILVER},
                {"text": getattr(self.preview_protein, "desc", ""), "mode": "static", "color": SILVER},
            ]
            boosts = getattr(self.preview_protein, "boosts", [])
            if boosts:
                content.append({"text": "Abilities:", "mode": "static", "color": LIGHT_BLUE})
                for boost in boosts:
                    boost_str = f"- {boost.get('type', '')}: {boost.get('amount', '')}"
                    content.append({"text": boost_str, "mode": "static", "color": SILVER})
        preview_panel = TextPanel((panel_x, panel_y, panel_w, panel_h), self.font, content, icon=icon)
        preview_panel.handle_event(event)

        # --- Codon menu scrolling and selection ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            codon_panel_x = 60
            codon_panel_y = 180
            codon_panel_w = 420
            codon_panel_h = 220
            line_height = self.font.get_height() + 6

            # Use the same codon order as in draw()
            from config import TYPE_CODON_MAP
            all_codons = sorted(TYPE_CODON_MAP.keys())
            if not hasattr(self.player, "discovered_codons"):
                self.player.discovered_codons = set()
            discovered = self.player.discovered_codons
            discovered_codons = [c for c in all_codons if c in discovered]
            undiscovered_codons = [c for c in all_codons if c not in discovered]
            codons = discovered_codons + undiscovered_codons

            if event.button == 4:  # scroll up
                self.codon_scroll = min(self.codon_scroll + self.codon_scroll_speed, 0)
            elif event.button == 5:  # scroll down
                self.codon_scroll -= self.codon_scroll_speed
            elif event.button == 1:
                # Click to select codon
                mouse_x, mouse_y = event.pos
                for i, codon in enumerate(codons):
                    y = codon_panel_y + 8 + (i * line_height) + self.codon_scroll
                    rect = pygame.Rect(codon_panel_x + 8, y, codon_panel_w - 16, line_height)
                    if rect.collidepoint(mouse_x, mouse_y):
                        if codon in self.player.discovered_codons:
                            self.selected_codon = codon
                        else:
                            self.selected_codon = None
                        break

    def craft_protein(self):
        sequence = self.seq_box.text.strip().upper()
        if sequence:
            from main import player_molecules, player_upgrades
            # Calculate costs
            required_protein = len(sequence) * 10  # 10 protein per codon
            required_nucleic_acid = len(sequence)  # 1 nucleic acid per letter typed
            
            # Check if we have enough resources
            if player_molecules.get('protein', 0) < required_protein:
                print("Not enough protein to craft!")
                return
            if player_molecules.get('nucleic_acid', 0) < required_nucleic_acid:
                print("Not enough nucleic acid to craft!")
                return
                
            # Create the protein
            self.seq_box.text = ""
            crafted = craft_protein(self.player, sequence)
            if not crafted:
                return
                
            # Pay the costs
            player_molecules['protein'] -= required_protein
            player_molecules['nucleic_acid'] -= required_nucleic_acid
            
            # Add to crafted proteins and mark codons as discovered
            crafted.is_crafted = True
            player_upgrades['Crafted Proteins'].append(crafted)
            print(f"Crafted {crafted.name}!\\n{crafted.desc}")
            
            # Discover codons
            if not hasattr(self.player, "discovered_codons"):
                self.player.discovered_codons = set()
            for i in range(0, len(sequence) - 2, 3):
                codon = sequence[i:i+3]
                if codon in TYPE_CODON_MAP:
                    self.player.discovered_codons.add(codon)

class UpgradeUI:
    def __init__(self, screen, player, close_menu_callback, selected_entities):
            self.screen = screen
            self.player = player
            self.font = pygame.font.SysFont("calibri", 20)
            self.bigfont = pygame.font.SysFont("calibri", 40)
            self.sections = [
                ("Proteins", ProteinsSectionUI),
                ("Organelles", OrganellesSectionUI),
                ("Crafting", ProteinCraftingUI),
                ("Inventory", InventorySectionUI),
            ]
            self.current_section = 0
            self.close_menu_callback = close_menu_callback
            self.back_button = Button((20, 20, 100, 40), "Back", self.close_menu_callback, self.font)
            self.tab_buttons = []
            self.section_uis = []
            for i, (name, cls) in enumerate(self.sections):
                x = 140 + i * 130
                self.tab_buttons.append(Button((x, 20, 120, 40), name, lambda i=i: self.set_section(i), self.font))
                if name == "Inventory":
                    self.section_uis.append(cls(screen, player, self.font, selected_entities))
                else:
                    self.section_uis.append(cls(screen, player, self.font))

    def set_section(self, index):
        self.current_section = index
        # Optionally reset section state if needed

    def update_selected_entities(self, selected_entities):
        """Update the list of selected entities in the inventory section."""
        # The inventory UI is the 4th section (index 3)
        if len(self.section_uis) > 3 and isinstance(self.section_uis[3], InventorySectionUI):
            self.section_uis[3].selected_entities = selected_entities

    def draw(self, delta_time):
        self.screen.fill((25, 25, 25))
        self.back_button.draw(self.screen)
        for i, button in enumerate(self.tab_buttons):
            button.draw(self.screen)
            if i == len(self.tab_buttons) - 2:
                pygame.draw.line(self.screen, (150, 150, 150), (button.rect.right + 5, 25), (button.rect.right + 5, 55), 2)
        section_name = self.sections[self.current_section][0]
        self.screen.blit(self.font.render(f"{section_name}", True, (255, 255, 0)), (30, 80))
        self.section_uis[self.current_section].draw(delta_time)

    def handle_event(self, event):
        self.back_button.handle_event(event)
        for button in self.tab_buttons:
            button.handle_event(event)
        self.section_uis[self.current_section].handle_event(event)

    def _debug_add_all_items(self):


        print("Debug: added all shop items to central inventory")

        
class SettingsMenuUI:
    def __init__(self, screen, close_menu_callback, return_to_main_menu_callback=None):
        self.screen = screen
        self.close_menu_callback = close_menu_callback
        self.return_to_main_menu_callback = return_to_main_menu_callback
        self.font = pygame.font.SysFont("calibri", 20)
        self.small_font = pygame.font.SysFont("calibri", 16)
        self.back_button = Button((20, 20, 100, 40), "Back", self.close_menu_callback, pygame.font.SysFont("calibri", 20))
        
        # Add Return to Main Menu button if callback is provided
        self.main_menu_button = None
        if return_to_main_menu_callback:
            self.main_menu_button = Button((SCREEN_WIDTH - 220, 20, 200, 40), "Return to Main Menu", 
                                         return_to_main_menu_callback, pygame.font.SysFont("calibri", 20))
        
        self.options = {
            "Music": True,
            "Sound FX": True,
            "Fullscreen": False
        }

    def draw(self, delta_time):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        self.back_button.draw(self.screen)
        
        # Draw Return to Main Menu button if available
        if self.main_menu_button:
            self.main_menu_button.draw(self.screen)

        title = self.font.render("Settings", True, SILVER)
        self.screen.blit(title, (self.screen.get_width() // 2 - title.get_width() // 2, 80))

        y = 150
        for key, value in self.options.items():
            option_text = f"{key}: {'On' if value else 'Off'}"
            rendered = self.small_font.render(option_text, True, LIGHT_BLUE)
            self.screen.blit(rendered, (self.screen.get_width() // 2 - rendered.get_width() // 2, y))
            y += 40

    def handle_event(self, event):
        self.back_button.handle_event(event)
        
        # Handle Return to Main Menu button if available
        if self.main_menu_button:
            self.main_menu_button.handle_event(event)
            
        # Handle other settings UI events here

class MapUI:
    """User interface for the world map (optimized/culling)"""
    def __init__(self, world_map):
        self.world_map = world_map
        self.is_open = False
        self.map_center = pygame.Vector2(0, 0)
        self.map_zoom = 0.1
        self.min_zoom = 0.1
        self.max_zoom = 1.0
        self.dragging = False
        self.drag_start_pos = None
        self.drag_start_map_center = None
        self.drag_moved = False
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def world_to_map_screen(self, world_pos):
        relative_pos = pygame.Vector2(world_pos) - self.map_center
        scale = SCREEN_WIDTH / (100000 * self.map_zoom)
        screen_pos = relative_pos * scale + pygame.Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        return screen_pos

    def get_visible_chunk_range(self):
        """Compute visible chunk indices based on current map view, using CHUNK_SIZE and clamped to WORLD_BOUNDS."""
        from math import floor
        top_left = self.map_screen_to_world((0, 0))
        bottom_right = self.map_screen_to_world((SCREEN_WIDTH, SCREEN_HEIGHT))
        csx, csy = CHUNK_SIZE
        min_chunk_x = floor(top_left.x / csx) - 1
        max_chunk_x = floor(bottom_right.x / csx) + 1
        min_chunk_y = floor(top_left.y / csy) - 1
        max_chunk_y = floor(bottom_right.y / csy) + 1
        # Clamp to world bounds
        min_idx_x = floor((-WORLD_BOUNDS[0] / 2) / csx)
        max_idx_x = floor((WORLD_BOUNDS[0] / 2 - 1) / csx)
        min_idx_y = floor((-WORLD_BOUNDS[1] / 2) / csy)
        max_idx_y = floor((WORLD_BOUNDS[1] / 2 - 1) / csy)
        min_chunk_x = max(min_chunk_x, min_idx_x)
        max_chunk_x = min(max_chunk_x, max_idx_x)
        min_chunk_y = max(min_chunk_y, min_idx_y)
        max_chunk_y = min(max_chunk_y, max_idx_y)
        return int(min_chunk_x), int(max_chunk_x), int(min_chunk_y), int(max_chunk_y)

    def map_screen_to_world(self, screen_pos):
        relative_pos = pygame.Vector2(screen_pos) - pygame.Vector2(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        scale = (100000 * self.map_zoom) / SCREEN_WIDTH
        world_pos = relative_pos * scale + self.map_center
        return world_pos

    def render_chunks(self, surface):
        min_chunk_x, max_chunk_x, min_chunk_y, max_chunk_y = self.get_visible_chunk_range()
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                # Render all chunks, including undiscovered ones (as black)
                chunk_key = (chunk_x, chunk_y)
                if chunk_key in self.world_map.world_generator.chunks:
                    chunk = self.world_map.world_generator.chunks[chunk_key]
                    self.render_chunk(surface, chunk)
                else:
                    # Create a temporary undiscovered chunk for rendering
                    from world_generation import Chunk, ChunkState
                    from config import CHUNK_SIZE
                    temp_chunk = type('TempChunk', (), {
                        'chunk_x': chunk_x,
                        'chunk_y': chunk_y, 
                        'state': ChunkState.UNDISCOVERED,
                        'biome': 'cold',
                        'world_rect': pygame.Rect(chunk_x * CHUNK_SIZE[0], chunk_y * CHUNK_SIZE[1], CHUNK_SIZE[0], CHUNK_SIZE[1])
                    })()
                    self.render_chunk(surface, temp_chunk)

    def render_chunk(self, surface, chunk):
        world_rect = chunk.world_rect
        top_left = self.world_to_map_screen((world_rect.left, world_rect.top))
        bottom_right = self.world_to_map_screen((world_rect.right, world_rect.bottom))
        screen_rect = pygame.Rect(int(top_left.x), int(top_left.y), int(bottom_right.x-top_left.x), int(bottom_right.y-top_left.y))
        if not screen_rect.colliderect(surface.get_rect()) or screen_rect.width <= 0 or screen_rect.height <= 0:
            return
        
        # Import chunk state and color constants
        from world_generation import ChunkState
        from config import MAP_UNDISCOVERED_COLOR, MAP_DISCOVERED_COLOR, MAP_VIEWED_COLOR
        
        # Choose base color based on chunk state
        if chunk.state == ChunkState.UNDISCOVERED:
            color = MAP_UNDISCOVERED_COLOR  # Black
        elif chunk.state == ChunkState.DISCOVERED:
            color = MAP_DISCOVERED_COLOR    # Dark gray  
        else:  # ChunkState.CELL_VIEWED
            color = MAP_VIEWED_COLOR        # Light gray
            
        pygame.draw.rect(surface, color, screen_rect)
        pygame.draw.rect(surface, (64,64,64), screen_rect, 1)
        
        # Only render biome overlay for discovered/viewed chunks with sufficient size
        if chunk.state != ChunkState.UNDISCOVERED and screen_rect.width > 4:
            from config import BIOMES
            biome_color = BIOMES[chunk.biome]["color"]
            
            # Adjust biome visibility based on zoom level
            # At high zoom (zoomed out), make biomes more visible
            # At low zoom (zoomed in), make biomes more subtle
            zoom_factor = self.map_zoom
            base_alpha = biome_color[3] if len(biome_color) > 3 else 80
            
            # Scale alpha based on zoom - more visible when zoomed out
            adjusted_alpha = min(255, int(base_alpha * (1.0 + zoom_factor * 0.5)))
            adjusted_biome_color = biome_color[:3] + (adjusted_alpha,)
            
            biome_rect = screen_rect.inflate(-2, -2)
            if biome_rect.width > 0 and biome_rect.height > 0:
                biome_surface = pygame.Surface((biome_rect.width, biome_rect.height), pygame.SRCALPHA)
                biome_surface.fill(adjusted_biome_color)
                surface.blit(biome_surface, biome_rect.topleft)
        
        # Render POI markers for ALL chunks (even undiscovered)
        if hasattr(chunk, 'poi_type') and chunk.poi_type and screen_rect.width > 8:
            center_x = screen_rect.centerx
            center_y = screen_rect.centery
            marker_size = max(6, min(20, int(screen_rect.width * 0.3)))
            
            # Purple question mark for all POI types
            pygame.draw.circle(surface, (128, 0, 128), (center_x, center_y), marker_size)
            pygame.draw.circle(surface, (200, 0, 200), (center_x, center_y), marker_size, 2)
            
            # Draw question mark if marker is big enough
            if marker_size >= 8:
                font_size = max(8, marker_size)
                poi_font = pygame.font.SysFont("arial", font_size, bold=True)
                question_text = poi_font.render("?", True, (255, 255, 255))
                text_rect = question_text.get_rect(center=(center_x, center_y))
                surface.blit(question_text, text_rect)

    def render_entities(self, surface, player_cells, all_entities):
        # Only draw entities in visible chunks
        min_chunk_x, max_chunk_x, min_chunk_y, max_chunk_y = self.get_visible_chunk_range()
        csx, csy = CHUNK_SIZE
        for cell in player_cells:
            pos = self.world_to_map_screen(cell.center)
            if 0 <= pos.x < SCREEN_WIDTH and 0 <= pos.y < SCREEN_HEIGHT:
                # Scale radius based on zoom - larger zoom = smaller radius, smaller zoom = larger radius
                base_radius = cell.radius * 0.05  # Scale down from world units (reduced from 0.1)
                radius = max(1, int(base_radius / self.map_zoom))
                color = getattr(cell, 'body_color', (0,255,0))
                pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), radius)
        for entity in all_entities:
            if hasattr(entity, 'center'):
                entity_pos = entity.center
            elif hasattr(entity, 'pos'):
                entity_pos = entity.pos
            else:
                continue
            chunk_x = int(entity_pos.x // csx)
            chunk_y = int(entity_pos.y // csy)
            if not (min_chunk_x <= chunk_x <= max_chunk_x and min_chunk_y <= chunk_y <= max_chunk_y):
                continue
            chunk = self.world_map.get_chunk_at_world_pos(entity_pos)
            if chunk.state == 2:
                pos = self.world_to_map_screen(entity_pos)
                if 0 <= pos.x < SCREEN_WIDTH and 0 <= pos.y < SCREEN_HEIGHT:
                    if hasattr(entity, 'is_player') and not entity.is_player:
                        color = (255,100,100) # Red for enemy
                    elif hasattr(entity, 'is_player') and entity.is_player:
                        continue # Already drawn above
                    else:
                        color = (255,255,0) # Yellow for other
                    # Use a smaller radius for non-player entities, scale with zoom
                    base_radius = getattr(entity, 'radius', 10) * 0.05  # Scale down from world units
                    radius = max(1, int(base_radius / self.map_zoom))
                    pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), radius)

    def open_map(self):
        """Open the map interface"""
        self.is_open = True
        
    def close_map(self):
        """Close the map interface"""
        self.is_open = False
        self.dragging = False  # Reset drag state when closing map
        
    def toggle_map(self):
        """Toggle map open/closed"""
        if self.is_open:
            self.close_map()
        else:
            self.open_map()
    
    def handle_event(self, events):
        """Handle input events for the map
        Returns: dict with 'handled' boolean and optional 'move_to' world position"""
        if not self.is_open:
            return {'handled': False}
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click - start dragging
                    self.dragging = True
                    self.drag_start_pos = pygame.Vector2(event.pos)
                    self.drag_start_map_center = self.map_center.copy()
                    self.drag_moved = False
                    return {'handled': True}
                elif event.button == 3:  # Right click - close map
                    self.close_map()
                    return {'handled': True}
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # End drag; if the mouse didn't move much, treat as a click
                    was_dragging = self.dragging
                    self.dragging = False
                    if not self.drag_moved:
                        world_pos = self.get_clicked_chunk_center(event.pos)
                        if world_pos:
                            return {'handled': True, 'move_to': world_pos}
                        return {'handled': True}
                    else:
                        return {'handled': True}
                    
            elif event.type == pygame.MOUSEMOTION:
                # If mouse not pressed anymore, cancel dragging
                if self.dragging and not pygame.mouse.get_pressed()[0]:
                    self.dragging = False
                    return {'handled': True}
                if self.dragging:
                    # Calculate drag delta and update map center
                    current_pos = pygame.Vector2(event.pos)
                    drag_delta = current_pos - self.drag_start_pos
                    # Mark as moved if beyond a small threshold (treat small movement as click)
                    if drag_delta.length_squared() > 25:  # 5px threshold
                        self.drag_moved = True
                    # Convert screen drag to world coordinates
                    world_drag_delta = drag_delta * self.map_zoom * 100000 / SCREEN_WIDTH
                    self.map_center = self.drag_start_map_center - world_drag_delta
                    return {'handled': True}
                
            elif event.type == pygame.MOUSEWHEEL:
                # Zoom in/out (reversed controls for map: scroll up = zoom out, scroll down = zoom in)
                zoom_factor = 1.0/1.1 if event.y > 0 else 1.1
                old_zoom = self.map_zoom
                self.map_zoom = max(self.min_zoom, min(self.max_zoom, self.map_zoom * zoom_factor))
                return {'handled': True}
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                    self.close_map()
                    return {'handled': True}
        
        return {'handled': False}
    
    def render_world_bounds(self, surface):
        """Render the world boundary lines"""
        from config import WORLD_BOUNDS
        # Get world bounds rectangle
        bounds_rect = pygame.Rect(
            -WORLD_BOUNDS[0]//2, -WORLD_BOUNDS[1]//2,
            WORLD_BOUNDS[0], WORLD_BOUNDS[1]
        )
        
        # Convert to screen coordinates
        top_left = self.world_to_map_screen((bounds_rect.left, bounds_rect.top))
        bottom_right = self.world_to_map_screen((bounds_rect.right, bounds_rect.bottom))
        
        screen_rect = pygame.Rect(
            int(top_left.x), int(top_left.y),
            int(bottom_right.x - top_left.x), int(bottom_right.y - top_left.y)
        )
        
        # Draw red boundary
        if screen_rect.width > 0 and screen_rect.height > 0:
            pygame.draw.rect(surface, (255, 0, 0), screen_rect, max(1, int(3 / self.map_zoom)))
    
    def render_legend(self, surface):
        """Render the map legend"""
        from config import MAP_UNDISCOVERED_COLOR, MAP_DISCOVERED_COLOR, MAP_VIEWED_COLOR
        legend_items = [
            ("Undiscovered", MAP_UNDISCOVERED_COLOR),
            ("Discovered", MAP_DISCOVERED_COLOR),
            ("Cell Viewed", MAP_VIEWED_COLOR),
            ("Player Cells", (0, 255, 0)),
            ("Enemy Cells", (255, 100, 100)),
            ("POI (Points of Interest)", (200, 0, 200)),
            ("World Bounds", (255, 0, 0))
        ]
        
        y_offset = 10
        for name, color in legend_items:
            # Draw color square
            pygame.draw.rect(surface, color, (10, y_offset, 15, 15))
            pygame.draw.rect(surface, (255, 255, 255), (10, y_offset, 15, 15), 1)
            
            # Draw text
            text = self.small_font.render(name, True, (255, 255, 255))
            surface.blit(text, (30, y_offset))
            
            y_offset += 20
    
    def render_coordinates(self, surface):
        """Render current map coordinates"""
        coord_text = f"Center: ({int(self.map_center.x)}, {int(self.map_center.y)})"
        zoom_text = f"Zoom: {self.map_zoom:.3f}"
        
        coord_surface = self.small_font.render(coord_text, True, (255, 255, 255))
        zoom_surface = self.small_font.render(zoom_text, True, (255, 255, 255))
        
        surface.blit(coord_surface, (SCREEN_WIDTH - 200, 10))
        surface.blit(zoom_surface, (SCREEN_WIDTH - 200, 30))
    
    def draw(self, surface, player_cells, all_entities):
        """Draw the complete map interface"""
        if not self.is_open:
            return
            
        # Fill background
        surface.fill((20, 20, 20))
        
        # Render chunks
        self.render_chunks(surface)
        
        # Render world bounds
        self.render_world_bounds(surface)
        
        # Render entities
        self.render_entities(surface, player_cells, all_entities)
        
        # Render UI elements
        self.render_legend(surface)
        self.render_coordinates(surface)
        
        # Render instructions
        instructions = [
            "Drag to pan, scroll to zoom",
            "Right-click or ESC/M to close"
        ]
        
        y_offset = SCREEN_HEIGHT - 40
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (200, 200, 200))
            surface.blit(text, (10, y_offset))
            y_offset += 20
    
    def get_clicked_chunk_center(self, mouse_pos):
        """
        Get the chunk that the mouse is clicking on and return the center of that chunk in world coordinates.
        
        Args:
            mouse_pos: Tuple of (x, y) screen coordinates where the mouse clicked
            
        Returns:
            pygame.Vector2: The center coordinates of the clicked chunk in world units, or None if no valid chunk
        """
        # Convert mouse screen position to world coordinates
        mouse_world_pos = self.map_screen_to_world(mouse_pos)
        return pygame.Vector2(mouse_world_pos.x, mouse_world_pos.y)
        
        # If no valid chunk found, return None
        print("failed to get chunk")
        return None

    def center_on_players(self, player_cells):
        """Center the map view on player cells"""
        if not player_cells:
            return
        
        # Calculate center of all player cells
        total_x = sum(cell.center.x for cell in player_cells)
        total_y = sum(cell.center.y for cell in player_cells)
        center_x = total_x / len(player_cells)
        center_y = total_y / len(player_cells)
        
        # Set map center to player center
        self.map_center_x = center_x
        self.map_center_y = center_y

class MainMenuUI:
    """Main menu screen with title and game mode selection"""
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.SysFont("calibri", 72, bold=True)
        self.font_button = pygame.font.SysFont("calibri", 32)
        self.font_subtitle = pygame.font.SysFont("calibri", 20)
        
        # Button dimensions and positions
        button_width = 200
        button_height = 60
        button_spacing = 20
        
        # Position buttons in right quadrants
        right_x = SCREEN_WIDTH - button_width - 100
        mid_y = SCREEN_HEIGHT // 2
        
        # Create buttons
        self.singleplayer_button = Button(
            (right_x, mid_y - button_height - button_spacing, button_width, button_height),
            "Singleplayer", 
            lambda: self.start_game_mode("singleplayer"),
            self.font_button
        )
        
        self.multiplayer_button = Button(
            (right_x, mid_y, button_width, button_height),
            "Multiplayer", 
            lambda: self.start_game_mode("multiplayer"),
            self.font_button
        )
        
        self.lab_button = Button(
            (right_x, mid_y + button_height + button_spacing, button_width, button_height),
            "Lab Mode", 
            lambda: self.start_game_mode("lab"),
            self.font_button
        )
        
        self.buttons = [self.singleplayer_button, self.multiplayer_button, self.lab_button]
        self.selected_mode = None
        
        # Background particles for visual appeal
        self.particles = []
        self.init_background_particles()
        
        # Initialize main menu simulation
        from main import spawn_main_menu_softbody
        spawn_main_menu_softbody()
    
    def init_background_particles(self):
        """Initialize floating background particles"""
        import random
        for _ in range(50):
            particle = {
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-20, 20),
                'size': random.randint(2, 6),
                'color': random.choice([(100, 150, 200), (150, 100, 200), (200, 150, 100)])
            }
            self.particles.append(particle)
    
    def start_game_mode(self, mode):
        """Set the selected game mode"""
        self.selected_mode = mode
    
    def update_particles(self, delta_time):
        """Update background particle animation"""
        for particle in self.particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            
            # Wrap around screen edges
            if particle['x'] < 0:
                particle['x'] = SCREEN_WIDTH
            elif particle['x'] > SCREEN_WIDTH:
                particle['x'] = 0
            if particle['y'] < 0:
                particle['y'] = SCREEN_HEIGHT
            elif particle['y'] > SCREEN_HEIGHT:
                particle['y'] = 0
    
    def draw_particles(self):
        """Draw background particles"""
        for particle in self.particles:
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])
    
    def draw(self, delta_time):
        """Draw the main menu"""
        # Clear screen with dark background
        self.screen.fill((20, 25, 35))
        
        # Update and draw main menu simulation
        from main import update_main_menu_simulation, draw_main_menu_simulation
        update_main_menu_simulation(delta_time)
        draw_main_menu_simulation(self.screen)
        
        # Update and draw background particles
        self.update_particles(delta_time)
        self.draw_particles()
        
        # Draw title "CellLab" in top-middle
        title_text = self.font_title.render("CellLab", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.font_subtitle.render("A Cellular Evolution Game", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 190))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
        
        # Draw status text for multiplayer
        status_text = self.font_subtitle.render("(Multiplayer coming soon!)", True, (150, 150, 150))
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(status_text, status_rect)
        
        # Draw version info
        version_text = self.font_subtitle.render("v1.0 - Congressional App Challenge", True, (100, 100, 100))
        version_rect = version_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.screen.blit(version_text, version_rect)
    
    def handle_event(self, event):
        """Handle main menu events"""
        for button in self.buttons:
            button.handle_event(event)
        
        return self.selected_mode

class DiscoveryEntry:
    """Represents a single discovery entry in the notebook"""
    def __init__(self, discovery_id, discovery_data, timestamp):
        self.id = discovery_id
        self.title = discovery_data["title"]
        self.description = discovery_data["description"]
        self.category = discovery_data["category"]
        self.educational_note = discovery_data.get("educational_note", "")
        self.timestamp = timestamp
        self.pinned = False
        self.height = 0  # Will be calculated during rendering
        self.is_custom = discovery_data.get("is_custom", False)  # Flag for custom notes

class NotebookUI:
    """Scientific discoveries notebook interface"""
    
    def __init__(self, screen, close_callback):
        self.screen = screen
        self.close_callback = close_callback
        self.is_open = False
        
        # Fonts
        self.font_title = pygame.font.SysFont("calibri", 24, bold=True)
        self.font_subtitle = pygame.font.SysFont("calibri", 18, bold=True)
        self.font_text = pygame.font.SysFont("calibri", 14)
        self.font_small = pygame.font.SysFont("calibri", 12)
        
        # Colors
        self.bg_color = (20, 25, 35, 240)
        self.entry_bg = (40, 50, 70)
        self.pinned_bg = (70, 80, 50)
        self.text_color = (200, 200, 200)
        self.title_color = (255, 255, 255)
        self.category_colors = {
            "Biology": (100, 200, 100),
            "Biochemistry": (200, 150, 100),
            "Genetics": (150, 100, 200),
            "Immunology": (200, 100, 100),
            "Evolution": (200, 200, 100),
            "Exploration": (100, 150, 200),
            "Cell Biology": (150, 200, 150),
            "Ecology": (100, 200, 150),
            "Biophysics": (200, 100, 150)
        }
        
        # UI dimensions
        self.width = SCREEN_WIDTH - 100
        self.height = SCREEN_HEIGHT - 100
        self.x = 50
        self.y = 50
        
        # Scroll state
        self.scroll_y = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        
        # Discoveries
        self.discoveries = []  # List of DiscoveryEntry objects
        self.discovered_ids = set()
        
        # Custom Notes System
        self.custom_notes = []  # List of custom note entries
        self.current_tab = "discoveries"  # "discoveries", "notes", or "leaderboard"
        self.note_input = ""
        self.is_typing_note = False
        
        # Buttons
        self.close_button = Button(
            (self.x + self.width - 80, self.y + 10, 70, 30),
            "Close", self.close_callback, self.font_text
        )
        
        # Tab buttons
        tab_width = 120
        tab_y = self.y + 60
        self.discoveries_tab = Button(
            (self.x + 20, tab_y, tab_width, 30),
            "Discoveries", lambda: self.switch_tab("discoveries"), self.font_text
        )
        self.notes_tab = Button(
            (self.x + 20 + tab_width + 10, tab_y, tab_width, 30),
            "My Notes", lambda: self.switch_tab("notes"), self.font_text
        )
        self.leaderboard_tab = Button(
            (self.x + 20 + (tab_width + 10) * 2, tab_y, tab_width, 30),
            "Leaderboard", lambda: self.switch_tab("leaderboard"), self.font_text
        )
        
        # Note input button
        self.add_note_button = Button(
            (self.x + 20, self.y + self.height - 40, 100, 30),
            "Add Note", self.start_note_input, self.font_text
        )
        
        # Initialize with welcome message
        if not self.discoveries:
            self._add_initial_entry()
        
        # Load custom notes from file
        self._load_custom_notes()
    
    def _add_initial_entry(self):
        """Add the initial welcome entry"""
        initial_data = {
            "title": "Scientific Discovery Notebook",
            "description": "This is the notebook. Look here for new discoveries! As you explore and experiment, your scientific findings will be documented here for future reference.",
            "category": "Introduction",
            "educational_note": "Science is built on observation, experimentation, and documentation of discoveries."
        }
        entry = DiscoveryEntry("initial", initial_data, 0)
        entry.pinned = True
        self.discoveries.append(entry)
        self.discovered_ids.add("initial")
    
    def add_discovery(self, discovery_id):
        """Add a new discovery to the notebook"""
        from config import DISCOVERIES
        
        if discovery_id in self.discovered_ids:
            return False  # Already discovered
        
        if discovery_id not in DISCOVERIES:
            return False  # Invalid discovery
        
        discovery_data = DISCOVERIES[discovery_id]
        import time
        entry = DiscoveryEntry(discovery_id, discovery_data, time.time())
        
        # Insert at beginning (after pinned entries)
        pinned_count = sum(1 for d in self.discoveries if d.pinned)
        self.discoveries.insert(pinned_count, entry)
        self.discovered_ids.add(discovery_id)
        
        return True
    
    def switch_tab(self, tab_name):
        """Switch between notebook tabs"""
        self.current_tab = tab_name
        self.scroll_y = 0
        self.is_typing_note = False
    
    def start_note_input(self):
        """Start typing a new note"""
        self.is_typing_note = True
        self.note_input = ""
    
    def add_custom_note(self, text):
        """Add a custom note to the notebook"""
        import time
        note_data = {
            "title": f"Personal Note - {time.strftime('%m/%d %H:%M')}",
            "description": text,
            "category": "Personal",
            "educational_note": "",
            "timestamp": time.time(),
            "is_custom": True
        }
        note_entry = DiscoveryEntry(f"custom_{len(self.custom_notes)}", note_data, time.time())
        self.custom_notes.insert(0, note_entry)  # Add to beginning
        self.is_typing_note = False
        self.note_input = ""
        self._save_custom_notes()  # Save to file
    
    def get_leaderboard_data(self):
        """Get global leaderboard data (simulated for now)"""
        # This would connect to a real server in production
        import random
        
        # Simulate some leaderboard data
        sample_data = [
            {"name": "CellMaster2024", "discoveries": 25, "achievements": ["Speed Demon", "Survivor", "Evolution Expert"]},
            {"name": "BiologyFan", "discoveries": 22, "achievements": ["Symbiosis", "Large Cell", "Viral Defense"]},
            {"name": "MicrobeExplorer", "discoveries": 20, "achievements": ["Ecosystem Explorer", "Organelle Creator"]},
            {"name": "EvolutionPro", "discoveries": 18, "achievements": ["Membrane Upgrade", "Protein Mastery"]},
            {"name": "ScienceKid", "discoveries": 15, "achievements": ["First Split", "Molecule Hunter"]},
        ]
        
        # Add player's current progress
        player_discoveries = len(self.discovered_ids)
        player_achievements = list(self.discovered_ids)[:5]  # Show first 5 as achievements
        
        player_entry = {
            "name": "You", 
            "discoveries": player_discoveries, 
            "achievements": player_achievements,
            "is_player": True
        }
        
        # Insert player in appropriate position
        inserted = False
        for i, entry in enumerate(sample_data):
            if player_discoveries >= entry["discoveries"]:
                sample_data.insert(i, player_entry)
                inserted = True
                break
        
        if not inserted:
            sample_data.append(player_entry)
        
        return sample_data[:10]  # Top 10
    
    def _save_custom_notes(self):
        """Save custom notes to file"""
        try:
            import json
            import os
            
            # Create saves directory if it doesn't exist
            saves_dir = "saves"
            if not os.path.exists(saves_dir):
                os.makedirs(saves_dir)
            
            # Prepare notes data for saving
            notes_data = []
            for note in self.custom_notes:
                note_dict = {
                    "title": note.title,
                    "description": note.description,
                    "category": note.category,
                    "timestamp": note.timestamp
                }
                notes_data.append(note_dict)
            
            # Save to file
            with open(os.path.join(saves_dir, "custom_notes.json"), 'w') as f:
                json.dump(notes_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save custom notes: {e}")
    
    def _load_custom_notes(self):
        """Load custom notes from file"""
        try:
            import json
            import os
            
            notes_file = os.path.join("saves", "custom_notes.json")
            if os.path.exists(notes_file):
                with open(notes_file, 'r') as f:
                    notes_data = json.load(f)
                
                # Convert back to DiscoveryEntry objects
                for note_dict in reversed(notes_data):  # Reverse to maintain order
                    note_dict["is_custom"] = True
                    note_dict["educational_note"] = ""
                    note_entry = DiscoveryEntry(f"custom_{len(self.custom_notes)}", note_dict, note_dict["timestamp"])
                    self.custom_notes.append(note_entry)
                    
        except Exception as e:
            print(f"Failed to load custom notes: {e}")
    
    def toggle_pin(self, entry):
        """Toggle pin status of an entry"""
        entry.pinned = not entry.pinned
        
        # Re-sort discoveries (pinned at top)
        self.discoveries.sort(key=lambda x: (not x.pinned, x.timestamp))
    
    def open(self):
        """Open the notebook"""
        self.is_open = True
        self.scroll_y = 0
    
    def close(self):
        """Close the notebook"""
        self.is_open = False
    
    def handle_event(self, event):
        """Handle notebook events"""
        if not self.is_open:
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.is_typing_note:
                    self.is_typing_note = False
                    self.note_input = ""
                else:
                    self.close()
            elif self.is_typing_note:
                # Handle note input
                if event.key == pygame.K_RETURN:
                    if self.note_input.strip():
                        self.add_custom_note(self.note_input.strip())
                elif event.key == pygame.K_BACKSPACE:
                    self.note_input = self.note_input[:-1]
                else:
                    # Add character to note input
                    if len(self.note_input) < 500:  # Limit note length
                        self.note_input += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check close button
                if self.close_button.rect.collidepoint(event.pos):
                    self.close()
                    return
                
                # Check tab buttons
                if self.discoveries_tab.rect.collidepoint(event.pos):
                    self.switch_tab("discoveries")
                    return
                elif self.notes_tab.rect.collidepoint(event.pos):
                    self.switch_tab("notes")
                    return
                elif self.leaderboard_tab.rect.collidepoint(event.pos):
                    self.switch_tab("leaderboard")
                    return
                
                # Check add note button (only in notes tab)
                if self.current_tab == "notes" and self.add_note_button.rect.collidepoint(event.pos):
                    self.start_note_input()
                    return
                
                # Check pin buttons
                content_rect = pygame.Rect(self.x + 20, self.y + 60, self.width - 40, self.height - 100)
                if content_rect.collidepoint(event.pos):
                    relative_y = event.pos[1] - content_rect.y + self.scroll_y
                    current_y = 0
                    
                    for entry in self.discoveries:
                        entry_height = self._calculate_entry_height(entry)
                        if current_y <= relative_y < current_y + entry_height:
                            # Check if clicked on pin button (top-right of entry)
                            pin_x = content_rect.right - 40
                            pin_y = content_rect.y + current_y - self.scroll_y + 5
                            pin_rect = pygame.Rect(pin_x, pin_y, 30, 20)
                            
                            if pin_rect.collidepoint(event.pos):
                                self.toggle_pin(entry)
                            break
                        current_y += entry_height + 10
            elif event.button == 3:  # Right click
                # Check if clicked on a discovery entry to open its URL
                content_rect = pygame.Rect(self.x + 20, self.y + 60, self.width - 40, self.height - 100)
                if content_rect.collidepoint(event.pos):
                    relative_y = event.pos[1] - content_rect.y + self.scroll_y
                    current_y = 0
                    
                    for entry in self.discoveries:
                        entry_height = self._calculate_entry_height(entry)
                        if current_y <= relative_y < current_y + entry_height:
                            # Found the clicked discovery entry
                            from config import DISCOVERIES
                            if entry.id in DISCOVERIES and "url" in DISCOVERIES[entry.id]:
                                discovery_url = DISCOVERIES[entry.id]["url"]
                                try:
                                    webbrowser.open(discovery_url)
                                    print(f"🔗 Opened educational link for '{entry.title}'")
                                except Exception as e:
                                    print(f"Failed to open URL for {entry.title}: {e}")
                            else:
                                print(f"No educational link available for '{entry.title}'")
                            break
                        current_y += entry_height + 10
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
            elif event.button == 5:  # Scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + self.scroll_speed)
    
    def _calculate_entry_height(self, entry):
        """Calculate the height needed for an entry"""
        base_height = 60  # Title + category
        
        # Description lines
        desc_lines = wrap_text(entry.description, self.font_text, self.width - 80)
        base_height += len(desc_lines) * 18
        
        # Educational note lines if present
        if entry.educational_note:
            note_lines = wrap_text(entry.educational_note, self.font_small, self.width - 80)
            base_height += len(note_lines) * 14 + 10
        
        return base_height
    
    def draw(self):
        """Draw the notebook interface"""
        if not self.is_open:
            return
        
        # Create surface with alpha
        notebook_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        notebook_surface.fill(self.bg_color)
        
        # Draw title bar
        title_rect = pygame.Rect(0, 0, self.width, 50)
        title_bg_color = (30, 40, 60)
        
        # Change title bar color when typing to indicate hotkeys are disabled
        if self.is_typing_note:
            title_bg_color = (60, 40, 30)  # Orange tint when typing
        
        pygame.draw.rect(notebook_surface, title_bg_color, title_rect)
        
        # Add typing indicator to title
        title_text_str = "Scientific Discovery Notebook"
        if self.is_typing_note:
            title_text_str += " - ⌨️ TYPING MODE (Hotkeys Disabled)"
        
        title_text = self.font_title.render(title_text_str, True, self.title_color)
        title_text_rect = title_text.get_rect(center=(self.width // 2, 25))
        notebook_surface.blit(title_text, title_text_rect)
        
        # Draw tab buttons
        self._draw_tab_button(notebook_surface, self.discoveries_tab, self.current_tab == "discoveries")
        self._draw_tab_button(notebook_surface, self.notes_tab, self.current_tab == "notes")
        self._draw_tab_button(notebook_surface, self.leaderboard_tab, self.current_tab == "leaderboard")
        
        # Draw content area based on current tab
        content_rect = pygame.Rect(20, 100, self.width - 40, self.height - 140)  # Adjust for tabs
        
        if self.current_tab == "discoveries":
            self._draw_discoveries_content(notebook_surface, content_rect)
        elif self.current_tab == "notes":
            self._draw_notes_content(notebook_surface, content_rect)
        elif self.current_tab == "leaderboard":
            self._draw_leaderboard_content(notebook_surface, content_rect)
        
        # Draw close button
        self.close_button.draw_on_surface(notebook_surface, (self.close_button.rect.x - self.x, self.close_button.rect.y - self.y))
        
        # Blit to main screen
        self.screen.blit(notebook_surface, (self.x, self.y))
    
    def _draw_tab_button(self, surface, button, is_active):
        """Draw a tab button with active/inactive styling"""
        color = (70, 80, 100) if is_active else (40, 50, 70)
        border_color = (120, 150, 180) if is_active else (80, 100, 120)
        
        # Adjust button position relative to notebook surface
        relative_rect = pygame.Rect(
            button.rect.x - self.x, button.rect.y - self.y,
            button.rect.width, button.rect.height
        )
        
        pygame.draw.rect(surface, color, relative_rect)
        pygame.draw.rect(surface, border_color, relative_rect, 2)
        
        text_color = (255, 255, 255) if is_active else (180, 180, 180)
        text_surface = self.font_text.render(button.text, True, text_color)
        text_rect = text_surface.get_rect(center=relative_rect.center)
        surface.blit(text_surface, text_rect)
    
    def _draw_discoveries_content(self, surface, content_rect):
        """Draw discoveries tab content"""
        # Calculate total content height for scrolling
        total_height = 0
        for entry in self.discoveries:
            total_height += self._calculate_entry_height(entry) + 10
        
        self.max_scroll = max(0, total_height - content_rect.height)
        
        # Create clipping surface for scrollable content
        content_surface = pygame.Surface((content_rect.width, content_rect.height))
        content_surface.fill((0, 0, 0, 0))
        
        # Draw entries
        current_y = -self.scroll_y
        for entry in self.discoveries:
            entry_height = self._calculate_entry_height(entry)
            
            # Only draw if visible
            if current_y + entry_height > 0 and current_y < content_rect.height:
                self._draw_entry(content_surface, entry, 0, current_y, content_rect.width)
            
            current_y += entry_height + 10
        
        surface.blit(content_surface, content_rect)
        
        # Draw scrollbar if needed
        if self.max_scroll > 0:
            scrollbar_height = max(20, int(content_rect.height * content_rect.height / total_height))
            scrollbar_y = int(self.scroll_y / self.max_scroll * (content_rect.height - scrollbar_height))
            scrollbar_rect = pygame.Rect(self.width - 15, content_rect.y, 10, scrollbar_height)
            pygame.draw.rect(surface, (100, 100, 100), scrollbar_rect)
    
    def _draw_notes_content(self, surface, content_rect):
        """Draw custom notes tab content"""
        # Calculate total content height for scrolling
        total_height = 0
        for entry in self.custom_notes:
            total_height += self._calculate_entry_height(entry) + 10
        
        # Add space for input box if typing
        if self.is_typing_note:
            total_height += 100
        
        self.max_scroll = max(0, total_height - content_rect.height)
        
        # Create clipping surface for scrollable content
        content_surface = pygame.Surface((content_rect.width, content_rect.height))
        content_surface.fill((0, 0, 0, 0))
        
        # Draw note input if typing
        current_y = -self.scroll_y
        if self.is_typing_note:
            self._draw_note_input(content_surface, 0, current_y, content_rect.width)
            current_y += 100
        
        # Draw custom notes
        for entry in self.custom_notes:
            entry_height = self._calculate_entry_height(entry)
            
            # Only draw if visible
            if current_y + entry_height > 0 and current_y < content_rect.height:
                self._draw_entry(content_surface, entry, 0, current_y, content_rect.width)
            
            current_y += entry_height + 10
        
        surface.blit(content_surface, content_rect)
        
        # Draw add note button
        if not self.is_typing_note:
            self.add_note_button.draw_on_surface(surface, (self.add_note_button.rect.x - self.x, self.add_note_button.rect.y - self.y))
        
        # Draw scrollbar if needed
        if self.max_scroll > 0 and total_height > 0:
            scrollbar_height = max(20, int(content_rect.height * content_rect.height / total_height))
            scrollbar_y = int(self.scroll_y / self.max_scroll * (content_rect.height - scrollbar_height))
            scrollbar_rect = pygame.Rect(self.width - 15, content_rect.y, 10, scrollbar_height)
            pygame.draw.rect(surface, (100, 100, 100), scrollbar_rect)
    
    def _draw_note_input(self, surface, x, y, width):
        """Draw the note input box"""
        input_rect = pygame.Rect(x, y, width, 80)
        pygame.draw.rect(surface, (40, 50, 70), input_rect)
        pygame.draw.rect(surface, (100, 150, 200), input_rect, 2)
        
        # Title
        title_text = self.font_subtitle.render("Type your note (Enter to save, Esc to cancel):", True, self.title_color)
        surface.blit(title_text, (x + 10, y + 5))
        
        # Input text with cursor
        display_text = self.note_input
        if len(display_text) > 60:  # Limit display length
            display_text = "..." + display_text[-57:]
        
        # Add blinking cursor
        import time
        if int(time.time() * 2) % 2:  # Blink every 0.5 seconds
            display_text += "|"
        
        input_text = self.font_text.render(display_text, True, self.text_color)
        surface.blit(input_text, (x + 10, y + 30))
        
        # Character count
        count_text = self.font_small.render(f"{len(self.note_input)}/500", True, (150, 150, 150))
        surface.blit(count_text, (x + width - 60, y + 60))
    
    def _draw_leaderboard_content(self, surface, content_rect):
        """Draw leaderboard tab content"""
        leaderboard_data = self.get_leaderboard_data()
        
        # Create content surface
        content_surface = pygame.Surface((content_rect.width, content_rect.height))
        content_surface.fill((0, 0, 0, 0))
        
        # Title
        title_text = self.font_subtitle.render("🏆 Global Discovery Leaderboard", True, (255, 215, 0))
        content_surface.blit(title_text, (10, 10))
        
        # Headers
        header_y = 50
        name_text = self.font_text.render("Player", True, self.title_color)
        discoveries_text = self.font_text.render("Discoveries", True, self.title_color)
        achievements_text = self.font_text.render("Recent Achievements", True, self.title_color)
        
        content_surface.blit(name_text, (10, header_y))
        content_surface.blit(discoveries_text, (200, header_y))
        content_surface.blit(achievements_text, (320, header_y))
        
        # Draw separator line
        pygame.draw.line(content_surface, (100, 100, 100), (10, header_y + 25), (content_rect.width - 20, header_y + 25), 2)
        
        # Draw leaderboard entries
        current_y = header_y + 40
        for i, player_data in enumerate(leaderboard_data):
            if current_y > content_rect.height - 30:
                break
                
            # Rank
            rank_text = self.font_text.render(f"#{i+1}", True, self.text_color)
            content_surface.blit(rank_text, (10, current_y))
            
            # Player name (highlight if it's the current player)
            name_color = (100, 255, 100) if player_data.get("is_player", False) else self.text_color
            name_text = self.font_text.render(player_data["name"], True, name_color)
            content_surface.blit(name_text, (50, current_y))
            
            # Discoveries count
            discoveries_text = self.font_text.render(str(player_data["discoveries"]), True, self.text_color)
            content_surface.blit(discoveries_text, (200, current_y))
            
            # Achievements (show first few)
            achievements = player_data.get("achievements", [])[:3]  # Show first 3
            achievement_str = ", ".join(achievements[:3])
            if len(achievements) > 3:
                achievement_str += "..."
            
            achievement_text = self.font_small.render(achievement_str, True, (180, 180, 180))
            content_surface.blit(achievement_text, (320, current_y))
            
            current_y += 25
        
        # Share button (placeholder for future implementation)
        share_y = content_rect.height - 60
        share_rect = pygame.Rect(10, share_y, 150, 30)
        pygame.draw.rect(content_surface, (50, 100, 150), share_rect)
        pygame.draw.rect(content_surface, (100, 150, 200), share_rect, 2)
        
        share_text = self.font_text.render("Share Progress", True, self.title_color)
        share_text_rect = share_text.get_rect(center=share_rect.center)
        content_surface.blit(share_text, share_text_rect)
        
        # Note about sharing
        note_text = self.font_small.render("🌐 Connect to internet to sync with global leaderboard", True, (150, 150, 150))
        content_surface.blit(note_text, (10, share_y + 40))
        
        surface.blit(content_surface, content_rect)
    
    def _draw_entry(self, surface, entry, x, y, width):
        """Draw a single discovery entry"""
        # Entry background
        bg_color = self.pinned_bg if entry.pinned else self.entry_bg
        entry_height = self._calculate_entry_height(entry)
        entry_rect = pygame.Rect(x, y, width, entry_height)
        pygame.draw.rect(surface, bg_color, entry_rect)
        pygame.draw.rect(surface, (60, 70, 90), entry_rect, 2)
        
        # Pin indicator
        if entry.pinned:
            pin_text = self.font_small.render("📌", True, (255, 255, 100))
            surface.blit(pin_text, (x + width - 35, y + 5))
        else:
            pin_text = self.font_small.render("📌", True, (100, 100, 100))
            surface.blit(pin_text, (x + width - 35, y + 5))
        
        # Title
        title_text = self.font_subtitle.render(entry.title, True, self.title_color)
        surface.blit(title_text, (x + 10, y + 10))
        
        # Category badge
        category_color = self.category_colors.get(entry.category, (100, 100, 100))
        category_text = self.font_small.render(entry.category, True, (255, 255, 255))
        category_rect = pygame.Rect(x + 10, y + 35, category_text.get_width() + 10, 20)
        pygame.draw.rect(surface, category_color, category_rect)
        surface.blit(category_text, (x + 15, y + 37))
        
        # Description
        current_y = y + 60
        desc_lines = wrap_text(entry.description, self.font_text, width - 20)
        for line in desc_lines:
            line_text = self.font_text.render(line, True, self.text_color)
            surface.blit(line_text, (x + 10, current_y))
            current_y += 18
        
        # Educational note
        if entry.educational_note:
            current_y += 10
            note_header = self.font_small.render("💡 Educational Note:", True, (255, 255, 150))
            surface.blit(note_header, (x + 10, current_y))
            current_y += 14
            
            note_lines = wrap_text(entry.educational_note, self.font_small, width - 20)
            for line in note_lines:
                line_text = self.font_small.render(line, True, (200, 200, 150))
                surface.blit(line_text, (x + 20, current_y))
                current_y += 14

# Helper method for Button class to draw on a surface
def _button_draw_on_surface(self, surface, offset):
    """Draw button on a given surface with offset"""
    color = (100, 100, 100) if self.hovered else (60, 60, 60)
    rect = pygame.Rect(offset[0], offset[1], self.rect.width, self.rect.height)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, (200, 200, 200), rect, 2)
    
    text_surface = self.font.render(self.text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# Add the method to Button class
Button.draw_on_surface = _button_draw_on_surface