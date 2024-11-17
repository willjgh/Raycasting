import pygame
import os
import math
import numpy as np
import pygame.gfxdraw
from profilehooks import profile
from copy import copy

rng = np.random.default_rng(255)

class Game:

    def __init__(self, window_width=700, window_height=700, canvas_width=150, canvas_height=150):

        # initialize pygame
        pygame.init()

        # configs
        pygame.display.set_caption("Raycaster")
        self.clock = pygame.time.Clock()
        self.dt = 0.0
        self.font = pygame.font.SysFont("Arial" , 18 , bold = True)

        # initialise window: high resolution, display
        self.window_width = window_width
        self.window_height = window_height
        self.window = pygame.display.set_mode((window_width, window_height))

        # canvas: low resolution, draw to
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.canvas = pygame.Surface((canvas_width, canvas_height))

        # camera: position and angle
        self.camera_position = [2.5, 2.5]
        self.camera_angle = 0.0
        self.camera_direction = [0.0, 1.0]
        self.plane_direction = [-1.0, 0.0]

        # field of view
        self.lambda_max = 1.0

        # construct grid
        self.m = 25
        self.n = 25
        self.grid = [[0 for j in range(self.n)] for i in range(self.m)]

        # fill with random scene
        for i in range(self.m):
            for j in range(self.n):
                u = rng.uniform()
                if u < 0.033:
                    self.grid[i][j] = 1
                elif u < 0.066:
                    self.grid[i][j] = 2
                elif u < 0.1:
                    self.grid[i][j] = 3

        # running flag
        self.running = True

    def framerate_counter(self):
        """Calculate and display frames per second."""
        # get fps
        fps = f"fps: {int(self.clock.get_fps())}"
        # create text
        fps_t = self.font.render(fps , 1, (0, 255, 0))
        # display on canvas
        self.window.blit(fps_t,(0, 0))

    def test_movement(self, x_movement, y_movement):
        '''Test if movement collides with grid, move if no issues'''

        # new position
        new_position_x = self.camera_position[0] + x_movement
        new_position_y = self.camera_position[1] + y_movement

        # new grid square
        new_grid_x = math.floor(new_position_x)
        new_grid_y = math.floor(new_position_y)

        # check if in grid
        if (new_grid_x >= 0) and (new_grid_x < self.n) and (new_grid_y >= 0) and (new_grid_y < self.n):

            # check if empty
            if self.grid[new_grid_y][new_grid_x] == 0:

                # update position
                self.camera_position = [new_position_x, new_position_y]

    
    def input(self):
        '''Take inputs'''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

        # get held keys
        keys = pygame.key.get_pressed()

        # movement scaled by time since last frame
        step = 0.005 * self.dt
        turn = 0.005 * self.dt
        
        # update camera position (if no collision) and camera angle
        if keys[pygame.K_w]:
            self.test_movement(self.camera_direction[0] * step, self.camera_direction[1] * step)
        if keys[pygame.K_s]:
            self.test_movement(-self.camera_direction[0] * step, -self.camera_direction[1] * step)
        if keys[pygame.K_a]:
            self.test_movement(-self.plane_direction[0] * step, -self.plane_direction[1] * step)
        if keys[pygame.K_d]:
            self.test_movement(self.plane_direction[0] * step, self.plane_direction[1] * step)
        if keys[pygame.K_LEFT]:
            self.camera_angle += turn
        if keys[pygame.K_RIGHT]:
            self.camera_angle -= turn

        # update camera and plane direction
        self.camera_direction = [np.sin(self.camera_angle), np.cos(self.camera_angle)]
        self.plane_direction = [-np.cos(self.camera_angle), np.sin(self.camera_angle)]

    def render(self):

        # draw background
        self.canvas.fill((0, 0, 0))

        # loop over each column of pixels on the canvas
        for x in range(self.canvas_width):

            # get corresponding ray direction
            lam = (((2 * x) / (self.canvas_width - 1)) - 1) * self.lambda_max
            ray_direction_x = self.camera_direction[0] + lam * self.plane_direction[0]
            ray_direction_y = self.camera_direction[1] + lam * self.plane_direction[1]
            ray_direction = [ray_direction_x, ray_direction_y]

            # raycast to get intersection
            intersection, intersection_distance, intersection_face, intersection_value = self.DDA(ray_direction)

            if intersection:

                # colour
                if intersection_value == 1:
                    if intersection_face:
                        colour = (0, 0, 255)
                    else:
                        colour = (0, 0, 150)
                elif intersection_value == 2:
                    if intersection_face:
                        colour = (0, 255, 0)
                    else:
                        colour = (0, 150, 0)
                elif intersection_value == 3:
                    if intersection_face:
                        colour = (255, 0, 0)
                    else:
                        colour = (150, 0, 0)
                
                # height of column inverse to distance
                column_height = 0.5 / intersection_distance

                # compute column limits on screen
                column_top = int(self.canvas_height * (1 - column_height) / 2)
                column_bottom = int(self.canvas_height * (1 + column_height) / 2)

                # cutoff to top and bottom of screen
                column_top = max(0, column_top)
                column_bottom = min(self.canvas_height, column_bottom)

                # draw pixel column
                for y in range(column_top, column_bottom + 1):

                    pygame.gfxdraw.pixel(self.canvas, x, y, colour)
        
        # blit surface to window
        self.window.blit(pygame.transform.scale(self.canvas, self.window.get_rect().size), (0, 0))
        self.framerate_counter()

        # update canvas
        pygame.display.flip()

    def DDA(self, ray_direction):

        # compute ray distance scaling for each axis 
        s_x = 1 / abs(ray_direction[0])
        s_y = 1 / abs(ray_direction[1])

        # intial grid position
        grid_x = math.floor(self.camera_position[0])
        grid_y = math.floor(self.camera_position[1])

        # initial distances to boundary of current grid square
        if ray_direction[0] < 0:
            step_x = -1
            ray_length_x = (self.camera_position[0] - grid_x) * s_x
        else:
            step_x = 1
            ray_length_x = (grid_x + 1 - self.camera_position[0]) * s_x
        
        if ray_direction[1] < 0:
            step_y = -1
            ray_length_y = (self.camera_position[1] - grid_y) * s_y
        else:
            step_y = 1
            ray_length_y = (grid_y + 1 - self.camera_position[1]) * s_y

        # cast ray until intersection
        intersection = False
        intersection_face = None
        intersection_value = None
        max_distance = 1000.0
        current_distance = 0.0

        while ((not intersection) and (current_distance < max_distance)):

            # choose smaller ray length axis
            if ray_length_x < ray_length_y:

                # step in x axis to new grid sqaure
                grid_x += step_x

                # store current distance to new grid square
                current_distance = ray_length_x

                # current intersection with x-axis face
                intersection_face = True

                # update ray length due to new step
                ray_length_x += s_x

            else:
                
                grid_y += step_y
                current_distance = ray_length_y
                intersection_face = False
                ray_length_y += s_y

            # check if intersection with new grid square
            if (grid_x >= 0) and (grid_x < self.n) and (grid_y >= 0) and (grid_y < self.n):

                intersection_value = self.grid[grid_y][grid_x]
                
                # check if empty
                if intersection_value != 0:
                    intersection = True
            else:
                break

        # threshold minimum distance: prevent zero division errors
        if current_distance < 0.1:
            current_distance = 0.1

        # return status and distance
        return intersection, current_distance, intersection_face, intersection_value


    def run(self):
        
        # loop
        while self.running:

            # clock
            self.dt = self.clock.tick()

            # take input
            self.input()

            # draw
            self.render()

        # quit
        pygame.quit()


@profile
def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()