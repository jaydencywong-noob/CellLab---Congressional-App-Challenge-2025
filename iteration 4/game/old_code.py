# Find the lowest available group number starting at 1
                    used_nums = set()
                    for key in cell_groups.keys():
                        if key.startswith("Group "):
                            try:
                                n = int(key.split(" ", 1)[1])
                                used_nums.add(n)
                            except Exception:
                                continue
                    next_num = 1
                    while next_num in used_nums:
                        next_num += 1
                    name = f"Group {next_num}"

                    # Enforce single-group membership: remove selected cells from any existing groups
                    empty_groups = []
                    for gname, members in cell_groups.items():
                        # iterate over a copy to avoid issues while removing
                        for c in list(members):
                            if c in grouped:
                                members.remove(c)
                                # clear previous group attribute
                                try:
                                    if getattr(c, 'group', None) == gname:
                                        setattr(c, 'group', None)
                                except Exception:
                                    pass
                        if len(members) == 0:
                            empty_groups.append(gname)
                    for gname in empty_groups:
                        # remove groups that have no members left
                        try:
                            del cell_groups[gname]
                            group_colors.pop(gname, None)
                            if camera_follow_group_key == gname:
                                # reset follow target
                                pass
                        except KeyError:
                            pass

                    # Create the new group with unique cells preserving order
                    cell_groups[name] = list(dict.fromkeys(grouped))
                    # Assign ONE random color to the group and set on all members
                    gcol = (random.randint(80, 255), random.randint(80, 255), random.randint(80, 255))
                    group_colors[name] = gcol
                    for c in cell_groups[name]:
                        c.body_color = gcol
                        try:
                            setattr(c, 'group', name)
                        except Exception:
                            pass
                    # Set camera to follow this group
                    camera_follow_group_key = name
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    # Check for clicks on any sprite
                    screen_pos = pygame.mouse.get_pos()
                    
                    # Only process clicks within the game screen bounds
                    if (0 <= screen_pos[0] <= SCREEN_WIDTH and 
                        0 <= screen_pos[1] <= SCREEN_HEIGHT):
                        world_pos = camera.screen_to_world(screen_pos)
                        clicked_any = False
                        
                        # Check player cells first
                        for cell in player_cells:
                            # Ensure cell has a center position
                            if not hasattr(cell, 'center'):
                                cell.center = cell.pos
                            if cell.center.distance_to(world_pos) < cell.radius * 1.2:  # Slightly larger click area
                                print(f"Clicked cell at {cell.center}, distance: {cell.center.distance_to(world_pos)}")
                                if cell in selected_entities:
                                    selected_entities.remove(cell)
                                else:
                                    # Clear other selections when selecting a new cell
                                    selected_entities.clear()
                                    selected_entities.append(cell)
                                clicked_any = True
                                break
                        
                        # Then check enemy cells
                        if not clicked_any:
                            for cell in enemy_cells:
                                if cell.center.distance_to(world_pos) < cell.radius:
                                    if cell in selected_entities:
                                        selected_entities.remove(cell)
                                    else:
                                        selected_entities.append(cell)
                                    clicked_any = True
                                    break
                        
                        # Finally check viruses
                        if not clicked_any:
                            for virus in viruses:
                                if virus.pos.distance_to(world_pos) < virus.radius:
                                    if virus in selected_entities:
                                        selected_entities.remove(virus)
                                    else:
                                        selected_entities.append(virus)
                                    break
                            # If no entity was clicked, move selected cells (only if some are selected)
                            if not clicked_any and selected_entities:
                                for entity in selected_entities:
                                    if isinstance(entity, PlayerCell):  # Only move cells
                                        entity.target_pos = camera.screen_to_world(screen_pos)

                        
                elif event.button == pygame.BUTTON_RIGHT and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # Start selection box
                    is_selecting = True
                    selection_box = (pygame.mouse.get_pos(), pygame.mouse.get_pos())
                    # Cancel any point selection for splitting
                    for cell in player_cells:
                        cell.split_points.clear()
            elif event.type == pygame.MOUSEMOTION and is_selecting:
                # Update selection box
                if selection_box:
                    selection_box = (selection_box[0], pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_RIGHT and is_selecting:
                    # Finish selection box
                    is_selecting = False
                if selection_box:
                    start, end = selection_box
                    x1, y1 = start
                    x2, y2 = end
                    left, right = sorted([x1, x2])
                    top, bottom = sorted([y1, y2])
                    selected_entities.clear()
                    # Check all selectable entities (player_cells, viruses, enemy_cells, etc.)
                    for entity in player_cells + viruses + enemy_cells:
                        screen_pos = camera.world_to_screen(entity.center)
                        if left <= screen_pos.x <= right and top <= screen_pos.y <= bottom:
                            selected_entities.append(entity)
                    
                    # Update the UI with the new selection
                    upgrade_ui.update_selected_entities(selected_entities)
                    
                    selection_box = None

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_menu == "settings":
                        close_menu()
                    elif current_menu is None:
                        open_menu("settings")
                elif event.key == pygame.K_SPACE:
                    # Toggle between selecting all and deselecting all player cells
                    if len(selected_entities) == len(player_cells) and all(cell in selected_entities for cell in player_cells):
                        # All cells are selected, deselect all
                        selected_entities.clear()
                        print("Deselected all player cells")
                    else:
                        # Not all cells are selected, select all
                        selected_entities.clear()
                        selected_entities.extend(player_cells)
                        print(f"Selected all {len(player_cells)} player cells")
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    # Use arrow keys to toggle camera position between groups
                    keys = _group_keys_sorted()
                    if keys:
                        nonlocal_camera_follow = camera_follow_group_key
                        if nonlocal_camera_follow in keys:
                            idx = keys.index(nonlocal_camera_follow)
                        else:
                            idx = 0
                        if event.key == pygame.K_LEFT:
                            idx = (idx - 1) % len(keys)
                        else:
                            idx = (idx + 1) % len(keys)
                        camera_follow_group_key = keys[idx]
                elif event.key == pygame.K_m:
                    # Toggle map view
                    map_ui.toggle_map()
                    if map_ui.is_open:
                        map_ui.center_on_players(player_cells)
            # Disable manual zoom: ignore mouse wheel in main view (map handles its own zoom)
            elif event.type == pygame.MOUSEWHEEL:
                pass



    #Spawn viruses and enemy cells periodically

    # Cleanup groups: remove cells that no longer exist; delete empty groups
    existing_set = set(player_cells)
    to_delete = []
    for gname, members in cell_groups.items():
        kept = []
        for c in members:
            if c in existing_set:
                kept.append(c)
            else:
                try:
                    if getattr(c, 'group', None) == gname:
                        setattr(c, 'group', None)
                except Exception:
                    pass
        cell_groups[gname] = kept
        if not kept:
            to_delete.append(gname)
    for gname in to_delete:
        del cell_groups[gname]
        group_colors.pop(gname, None)
        if camera_follow_group_key == gname:
            camera_follow_group_key = None

    # Derive a view size based on current camera zoom (avoid division by zero)
    effective_zoom = max(0.25, camera.zoom)
    size_h = int(SCREEN_HEIGHT / effective_zoom)
    size_w = int(SCREEN_WIDTH / effective_zoom)
    half_size_h = size_h//2
    half_size_w = size_w//2

    bounding_box = pygame.Rect(camera.pos.x-half_size_w, camera.pos.y-half_size_h, size_w, size_h)
    screen_box = pygame.Rect(camera.world_to_screen((bounding_box.left, bounding_box.top)), (size_w*camera.zoom, size_h*camera.zoom))

    min_spawn_distance = 1000  # Minimum distance from any player cell (increased for better gameplay)

    # Procedural enemy generation near groups
    def _random_point_near(center: pygame.Vector2, min_d: float, max_d: float) -> pygame.Vector2:
        ang = random.uniform(0, 3.14159 * 2)
        dist = random.uniform(min_d, max_d)
        return pygame.Vector2(center.x + dist * math.cos(ang), center.y + dist * math.sin(ang))

    def _get_chunk_for_pos(pos):
        return world_map.get_chunk_at_world_pos(pos)

    def _chunk_has_enemy(chunk):
        # Check if chunk contains any enemy cells or viruses
        for cell in enemy_cells:
            if _get_chunk_for_pos(cell.center) == chunk:
                return True
        for virus in viruses:
            if _get_chunk_for_pos(virus.pos) == chunk:
                return True
        return False

    def _spawn_enemy_at(pos: pygame.Vector2, enemy_kind: str):
        chunk = _get_chunk_for_pos(pos)
        if chunk and _chunk_has_enemy(chunk):
            return  # Mob cap reached, do not spawn
        if enemy_kind == 'rogue-virus':
            spawn_virus(pos)
        elif enemy_kind == 'rogue-cell':
            spawn_enemy_cell(pos)
        elif enemy_kind == 'pack-capsid':
            # Spawn pack in a large radius
            for _ in range(random.randint(3, 6)):
                pack_pos = _random_point_near(pos, 1200, 2000)
                pack_chunk = _get_chunk_for_pos(pack_pos)
                if pack_chunk and not _chunk_has_enemy(pack_chunk):
                    spawn_virus(pack_pos)
        elif enemy_kind == 'pack-cells':
            for _ in range(random.randint(3, 6)):
                pack_pos = _random_point_near(pos, 1200, 2000)
                pack_chunk = _get_chunk_for_pos(pack_pos)
                if pack_chunk and not _chunk_has_enemy(pack_chunk):
                    spawn_enemy_cell(pack_pos)

    # Choose a group center as focus for spawns
    group_keys = [k for k, v in cell_groups.items() if v]
    group_centers = []
    for k in group_keys:
        members = cell_groups[k]
        if not members:
            continue
        c = pygame.Vector2(0, 0)
        for m in members:
            c += m.center
        group_centers.append(c / len(members))

    # Low probability each frame; scale with delta_time
    if group_centers and random.random() < 0.02 * (delta_time * 60.0):
        center = random.choice(group_centers)
        spawn_type = random.choice(['rogue-virus', 'rogue-cell', 'pack-capsid', 'pack-cells'])
        # pick a valid spawn pos not too close to player cells
        for _ in range(8):
            pos = _random_point_near(center, 400, 900)
            chunk = _get_chunk_for_pos(pos)
            if chunk and not _chunk_has_enemy(chunk) and all(pos.distance_to(cell.center) > min_spawn_distance for cell in player_cells):
                _spawn_enemy_at(pos, spawn_type)
                break

    # Game update logic
    if current_menu is None:
        # Update all player cells
        for cell in player_cells:
            cell.update(screen, events, delta_time, camera)
            for u in cell.organelle_slots:
                if u and u.name == "Cell Membrane Extender":
                    # Add new membrane points
                    cell.extend_membrane(10)
                    # Increase radius
                    cell.radius += 10
                    # Redistribute all points and springs into a larger circle
                    cell.redistribute_points_to_circle(cell.radius)
                    # Update shape and area calculations
                    cell.initial_shape = cell.calculate_shape()
                    cell.rest_area = cell.calculate_area()
                    # Remove the extender after use
                    cell.organelle_slots[cell.organelle_slots.index(u)] = None
        
        # Update targeting system for all player cells
        import time
        current_time = time.time()
        all_enemies = viruses + enemy_cells  # Combine all potential targets
        all_entities = player_cells + enemy_cells + viruses  # All entities for abilities
        
        for cell in player_cells:
            cell.update_targeting(current_time, all_enemies)
            cell.maintain_target_distance(delta_time)
            cell.update_protein_abilities(delta_time, all_entities, current_time)
        

        for cell in player_cells:
            if cell.split_body():
                random_vector = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                sb1, sb2, old_body = cell.split_body()
                player_cells.append(sb1)
                sb1.pos += random_vector * sb1.points[0].pos.distance_to(sb1.points[1].pos)*2
                sb1.is_player = True
                sb1.atp = old_body.atp // 2
                player_cells.append(sb2)
                sb2.pos += random_vector * -sb2.points[0].pos.distance_to(sb2.points[1].pos)*2
                sb2.is_player = True
                sb2.atp = old_body.atp // 2
                sb1.target_pos = sb1.pos
                sb2.target_pos = sb2.pos
                player_cells.remove(old_body)
                sb1.radius = max(10, sb1.radius * 0.75) 
                sb2.radius = max(10, sb2.radius * 0.75)
                
                # Update selected entities if the split cell was selected
                if old_body in selected_entities:
                    selected_entities.remove(old_body)
                    selected_entities.append(sb1)  # Select one of the new cells
                break

        for virus in viruses:
            all_cells = player_cells + enemy_cells
            virus.update(all_cells, delta_time)
            
            # Check for virus-cell collisions
            for cell in all_cells:
                # Check if virus is close enough to attack
                distance = virus.pos.distance_to(cell.center)
                if distance < (virus.radius + cell.radius):
                    import time
                    current_time = time.time()
                    cell_killed = virus.attack_cell(cell, current_time)
                    
                    if cell_killed:
                        # Cell will be removed by health check below
                        pass
                    break

        for cell in enemy_cells:
            cell.update(screen, events, delta_time, camera)
        
        # Handle cell deaths and drop molecules
        dying_player_cells = [cell for cell in player_cells if cell.health <= 0]
        dying_enemy_cells = [cell for cell in enemy_cells if cell.health <= 0]
        
        # Drop molecules from dying cells
        for cell in dying_player_cells + dying_enemy_cells:
            dropped_molecules = cell.drop_upgrade_molecules()
            
            # Add dropped molecules to the world
            if dropped_molecules:
                # Find the appropriate chunk to add molecules to
                chunk = world_map.get_chunk_at_world_pos(cell.center)
                if chunk:
                    chunk.molecules.extend(dropped_molecules)
                    print(f"Cell death dropped {len(dropped_molecules)} molecules at {cell.center}")
        
        # Remove dead cells after handling drops
        player_cells[:] = [cell for cell in player_cells if cell.health > 0]
        enemy_cells[:] = [cell for cell in enemy_cells if cell.health > 0]
        
        # Remove dead viruses
        viruses[:] = [virus for virus in viruses if virus.health > 0]
        
        # Process pending virus spawns
        for spawn_data in pending_virus_spawns:
            virus_type = spawn_data['type']
            pos = spawn_data['pos']
            size = spawn_data['size']
            
            # Create virus based on type
            if virus_type.__name__ == 'CapsidVirus':
                new_virus = CapsidVirus(pos, size, max(2, size//2))
            elif virus_type.__name__ == 'FilamentousVirus':
                new_virus = FilamentousVirus(pos, length=size*4, spacing=size//2, radius=size)
            elif virus_type.__name__ == 'PhageVirus':
                new_virus = PhageVirus(pos, radius=size, points=max(2, size//2))
            else:
                continue
                
            viruses.append(new_virus)
            sprites.append(new_virus)
        
        # Clear processed spawns
        pending_virus_spawns.clear()

        # Resolve collisions using spatial partitioning collision system
        all_cells = player_cells + enemy_cells
        if len(all_cells) > 1:
            # Use the improved CollisionSystem with spatial partitioning
            collision_system.detect_and_resolve_collisions(all_cells)
            
            # Handle cell vs cell combat collisions
            import time
            current_time = time.time()
            
            # Check for combat situations (player vs enemy)
            for player_cell in player_cells:
                for enemy_cell in enemy_cells:
                    distance = player_cell.center.distance_to(enemy_cell.center)
                    collision_distance = player_cell.radius + enemy_cell.radius - 10  # Small buffer
                    
                    if distance < collision_distance:
                        # Handle combat
                        winner, loser = player_cell.handle_collision_combat(enemy_cell, current_time)
                        break  # Only one combat per frame per cell

        # Update external springs (inter-cell connections)
        for spring in external_springs[:]:  # Use slice to allow safe removal during iteration
            spring.update(delta_time)
            if not spring.active:
                external_springs.remove(spring)
        
        # Update connection chains and apply snake-like movement
        connection_manager.update_chains(external_springs, all_cells)
        connection_manager.apply_snake_movement(delta_time)
        
        # Handle molecule collection by player cells
        for cell in player_cells:
            for chunk in world_map.world_generator.chunks.values():
                from world_generation import ChunkState
                if chunk.state != ChunkState.UNDISCOVERED:
                    molecules_to_remove = []
                    for mol in chunk.molecules:
                        # Check collision between cell and molecule
                        distance = cell.center.distance_to(mol.pos)
                        if distance < cell.radius + getattr(mol, 'radius', 15):  # Molecule collection radius
                            # Add to central inventory
                            mol_type_name = type(mol).__name__.lower()
                            # Handle nucleicacid -> nucleic_acid mapping
                            if mol_type_name == "nucleicacid":
                                mol_type_name = "nucleic_acid"
                            if mol_type_name in player_molecules:
                                mol_value = getattr(mol, 'value', 1)  # Use molecule's value, default to 1
                                player_molecules[mol_type_name] += mol_value
                                molecules_to_remove.append(mol)
                                print(f"Collected {type(mol).__name__} worth {mol_value}! Total: {player_molecules[mol_type_name]}")
                    
                    # Remove collected molecules from chunk
                    for mol in molecules_to_remove:
                        chunk.molecules.remove(mol)

        def _compute_zoom_for_cells(cells):
            # Compute zoom to fit cells with padding in screen
            if not cells:
                return camera.zoom
            if len(cells) == 1:
                return min(0.75, max(0.25, 1.2))
            xs = [c.center.x for c in cells]
            ys = [c.center.y for c in cells]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max(20.0, max_x - min_x)
            height = max(20.0, max_y - min_y)
            padding = 1.6  # fit with extra space
            # Effective zoom so that world extent * zoom ~ screen extent / padding
            zx = (SCREEN_WIDTH / padding) / width
            zy = (SCREEN_HEIGHT / padding) / height
            z = min(zx, zy)
            return min(0.75, max(1, z))

        # Set camera target group
        focus_cells = None
        if camera_follow_group_key and camera_follow_group_key in cell_groups and cell_groups[camera_follow_group_key]:
            focus_cells = cell_groups[camera_follow_group_key]
        elif selected_entities:
            # fallback: selected entities that are player cells
            from player import PlayerCell
            focus_cells = [e for e in selected_entities if isinstance(e, PlayerCell)]
        else:
            focus_cells = player_cells

        if focus_cells:
            # Center camera on average of focus cells
            total_masses = pygame.Vector2(0, 0)
            for cell in focus_cells:
                total_masses += cell.center
            camera.pos = total_masses / len(focus_cells)
            # Compute zoom based on furthest spread of focus cells
            camera.zoom = _compute_zoom_for_cells(focus_cells)
        
        # Get molecules from discovered chunks dynamically
        molecules = world_map.get_molecules_in_discovered_chunks()
        
        # Update world generation and chunk discovery
        all_entities = player_cells + enemy_cells + viruses + molecules
        world_map.update(player_cells, all_entities)
        
        # Handle POI spawning from discovered chunks
        for chunk in world_map.world_generator.chunks.values():
            # Handle virus cluster spawns
            if hasattr(chunk, 'pending_virus_spawns'):
                from virus import CapsidVirus, FilamentousVirus, PhageVirus
                for spawn_data in chunk.pending_virus_spawns:
                    virus_type = spawn_data['virus_type']
                    pos = spawn_data['position']
                    size = spawn_data['size']
                    
                    # Scale down POI virus sizes too
                    small_size = max(10, size // 4)  # Make POI viruses smaller
                    if virus_type.__name__ == "CapsidVirus":
                        virus = virus_type(pos, small_size, small_size//2)
                    elif virus_type.__name__ == "FilamentousVirus":
                        virus = virus_type(pos, length=small_size*4, spacing=small_size//2, radius=small_size)
                    elif virus_type.__name__ == "PhageVirus":
                        virus = virus_type(pos, radius=small_size, points=small_size//2)
                    
                    viruses.append(virus)
                    sprites.append(virus)
                
                # Clear pending spawns
                del chunk.pending_virus_spawns
            
            # Handle giant enemy spawns  
            if hasattr(chunk, 'pending_enemy_spawn'):
                from entity import Cell
                from molecule import Lipid
                spawn_data = chunk.pending_enemy_spawn
                giant_cell = Cell(spawn_data['position'], points=spawn_data['points'], 
                                radius=spawn_data['radius'], membrane_molecule=Lipid)
                enemy_cells.append(giant_cell)
                sprites.append(giant_cell)
                
                # Clear pending spawn
                del chunk.pending_enemy_spawn
        
        # Update visual systems
        visuals.update_visual_systems(delta_time)
        
        # Generate particles from molecules
        visuals.create_molecule_particles(molecules, camera)

    camera_offset = camera.pos - pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_scrolling_background(screen, background_tile, camera_offset, camera)
    
    # Render world boundaries, chunk backgrounds, and biome overlays
    if current_menu is None and not map_ui.is_open:
        world_map.render_world_boundaries(screen, camera)
        world_map.render_chunk_backgrounds(screen, camera)  # Add chunk state backgrounds
        world_map.render_biome_overlay(screen, camera)
    
    # Optional dark background for better visual effects (currently disabled)
    # screen.fill((5, 10, 15))  # Very dark blue-black

    # Drawing UI
    if current_menu == "upgrade":
        upgrade_ui.draw(delta_time)
    elif current_menu == "settings":
        settings_ui.draw(delta_time)
    else:
        # Draw selection box if active
        if is_selecting and selection_box:
            start, end = selection_box
            rect = pygame.Rect(*start, *(pygame.Vector2(end) - pygame.Vector2(start)))
            rect.normalize()
            pygame.draw.rect(screen, (100, 200, 255, 80), rect, 2)
        
        # Draw targeting lines for player cells
        for cell in player_cells:
            if hasattr(cell, 'current_target') and cell.current_target:
                target = cell.current_target
                target_pos = target.center if hasattr(target, 'center') else target.pos
                
                # Draw targeting line (different color for damaged_by priority)
                if cell.damaged_by == target:
                    line_color = (255, 50, 50)  # Red for revenge target
                else:
                    line_color = (255, 200, 50)  # Yellow for normal target
                
                # Draw a dashed line effect
                cell_screen_pos = camera.world_to_screen(cell.center)
                target_screen_pos = camera.world_to_screen(target_pos)
                
                # Calculate line direction and draw segments
                direction = target_screen_pos - cell_screen_pos
                distance = direction.length()
                if distance > 0:
                    direction.normalize_ip()
                    dash_length = 10
                    gap_length = 5
                    current_pos = cell_screen_pos.copy()
                    drawn = 0
                    
                    while drawn < distance:
                        next_pos = current_pos + direction * min(dash_length, distance - drawn)
                        pygame.draw.line(screen, line_color, current_pos, next_pos, 2)
                        current_pos = next_pos + direction * gap_length
                        drawn += dash_length + gap_length
                
                # Draw crosshair on target
                pygame.draw.circle(screen, line_color, target_screen_pos, 15, 2)
                pygame.draw.line(screen, line_color, 
                               (target_screen_pos.x - 10, target_screen_pos.y), 
                               (target_screen_pos.x + 10, target_screen_pos.y), 2)
                pygame.draw.line(screen, line_color,
                               (target_screen_pos.x, target_screen_pos.y - 10), 
                               (target_screen_pos.x, target_screen_pos.y + 10), 2)
        
        # Draw player cells with visual effects
        for cell in player_cells:
            # Only draw path line for this specific cell's target, not all selected cells' targets
            if cell in selected_entities and hasattr(cell, 'target_pos'):
                pygame.draw.line(screen, (150, 150, 255), camera.world_to_screen(cell.center), camera.world_to_screen(cell.target_pos), 5)
                pygame.draw.circle(screen, (150, 100, 255), camera.world_to_screen(cell.target_pos), 10, 2)
                pygame.draw.line(screen, (255, 165, 0), camera.world_to_screen(cell.center), camera.world_to_screen(cell.velocity+cell.center), 5)
            
            # Draw cell with visual effects
            visuals.draw_cell_with_effects(screen, cell, camera, delta_time, enable_effects=True)
            
            # Draw protein abilities (projectiles, shields, mines, webs)
            cell.draw_protein_abilities(screen, camera)
            

        # Helper function to check if entity should be visible
        def is_entity_visible(entity_pos):
            chunk = world_map.get_chunk_at_world_pos(entity_pos)
            from world_generation import ChunkState
            return chunk and chunk.state != ChunkState.UNDISCOVERED

        # Draw enemy cells with visual effects (only if in discovered chunks)
        for cell in enemy_cells:
            if is_entity_visible(cell.center):
                visuals.draw_cell_with_effects(screen, cell, camera, delta_time, enable_effects=True)

        # Draw viruses (only if in discovered chunks)
        for virus in viruses:
            if is_entity_visible(virus.pos):
                virus.draw(screen, camera)

        # Draw molecules with visual effects (only if in discovered chunks)
        for mol in molecules:
            if is_entity_visible(mol.pos):
                visuals.draw_molecule_with_effects(screen, mol, camera, delta_time, enable_effects=True)
        
        # Draw external spring connections between cells
        for spring in external_springs:
            spring.draw(screen, camera)
        
        # Draw visual effects (particles, trails, etc.)
        visuals.draw_visual_systems(screen, camera)

        game_ui.draw(delta_time)
        # Draw the cell manager under stats on the left
        try:
            cell_manager_ui.draw(screen)
        except NameError:
            pass
        # Draw header buttons only when not in the upgrade menu
        if current_menu != "upgrade":
            upgrade_button.draw(screen)
            settings_button.draw(screen)
            map_button.draw(screen)

    #pygame.draw.rect(screen, DARK_BLUE, screen_box, 0)
    # Draw map UI if open (always drawn on top)
    if map_ui.is_open:
        molecules = world_map.get_molecules_in_discovered_chunks()
        all_entities = player_cells + enemy_cells + viruses + molecules
        map_ui.draw(screen, player_cells, all_entities)

    pygame.display.flip()
    delta_time = clock.tick(FPS) / 1000.0  # Convert milliseconds to seconds

pygame.quit()