import pygame
import os
import math
import numpy as np
import pygame.gfxdraw
from profilehooks import profile

rng = np.random.default_rng(255)

class Game:

    def __init__(self, window_width=700, window_height=700, canvas_width=200, canvas_height=200):

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

        # grid
        self.m = 25
        self.n = 25
        self.grid = [[0 for j in range(self.n)] for i in range(self.m)]

        for i in range(self.m):
            for j in range(self.n):
                u = rng.uniform()
                if u < 0.1:
                    self.grid[i][j] = 1

        # running flag
        self.running = True

    def framerate_counter(self):
        """Calculate and display frames per second."""
        # get fps
        fps = str(int(self.clock.get_fps()))
        pos = f"pos: {self.camera_position[0]}, {self.camera_position[1]}"
        ang = f"ang: {self.camera_angle}"
        cam = f"cam: {self.camera_direction[0]}, {self.camera_direction[1]}"
        pln = f"pln: {self.plane_direction[0]}, {self.plane_direction[1]}"
        # create text
        fps_t = self.font.render(fps , 1, (0, 255, 0))
        pos_t = self.font.render(pos, 1, (0, 255, 0)) 
        ang_t = self.font.render(ang, 1, (0, 255, 0))
        cam_t = self.font.render(cam, 1, (0, 255, 0))
        pln_t = self.font.render(pln, 1, (0, 255, 0))
        # display on canvas
        self.window.blit(fps_t,(0, 18 * 0))
        self.window.blit(pos_t,(0, 18 * 1))
        self.window.blit(ang_t,(0, 18 * 2))
        self.window.blit(cam_t,(0, 18 * 3))
        self.window.blit(pln_t,(0, 18 * 4))

    
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
        
        # update camera position and angle
        if keys[pygame.K_w]:
            # self.camera_position[1] += step
            self.camera_position[0] += self.camera_direction[0] * step
            self.camera_position[1] += self.camera_direction[1] * step
        if keys[pygame.K_s]:
            # self.camera_position[1] -= step
            self.camera_position[0] -= self.camera_direction[0] * step
            self.camera_position[1] -= self.camera_direction[1] * step
        if keys[pygame.K_a]:
            # self.camera_position[0] += step
            self.camera_position[0] -= self.plane_direction[0] * step
            self.camera_position[1] -= self.plane_direction[1] * step
        if keys[pygame.K_d]:
            # self.camera_position[0] -= step
            self.camera_position[0] += self.plane_direction[0] * step
            self.camera_position[1] += self.plane_direction[1] * step
        if keys[pygame.K_LEFT]:
            self.camera_angle += turn
        if keys[pygame.K_RIGHT]:
            self.camera_angle -= turn

        # update camera and plane direction
        self.camera_direction = [np.sin(self.camera_angle), np.cos(self.camera_angle)] #[-np.sin(self.camera_angle), np.cos(self.camera_angle)]
        self.plane_direction = [-np.cos(self.camera_angle), np.sin(self.camera_angle)] #[np.cos(self.camera_angle), np.sin(self.camera_angle)]

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
            '''may need to normalize'''

            # raycast to get intersection
            intersection, intersection_distance, intersection_x = self.DDA(ray_direction)

            if intersection:

                # colour
                if intersection_x:

                    colour = (255, 0, 0)
                
                else:
                    
                    colour = (0, 0, 255)

                # height of column inverse to distance
                column_height = 100 / intersection_distance

                # compute column limits on screen
                column_top = int((self.canvas_height / 2) - (column_height / 2))
                column_bottom = int((self.canvas_height / 2) + (column_height / 2))

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

        '''can simplify if normalized'''
        # compute scaling
        s_x = math.sqrt(1 + (ray_direction[1] / ray_direction[0])**2)
        s_y = math.sqrt(1 + (ray_direction[0] / ray_direction[1])**2)

        # intial grid position
        grid_x = math.floor(self.camera_position[0])
        grid_y = math.floor(self.camera_position[1])

        # initial distances
        if ray_direction[0] < 0:
            step_x = -1
            ray_length_x = (self.camera_position[0] - math.floor(self.camera_position[0])) * s_x
        else:
            step_x = 1
            ray_length_x = (math.ceil(self.camera_position[0]) - self.camera_position[0]) * s_x
        
        if ray_direction[1] < 0:
            step_y = -1
            ray_length_y = (self.camera_position[1] - math.floor(self.camera_position[1])) * s_y
        else:
            step_y = 1
            ray_length_y = (math.ceil(self.camera_position[1]) - self.camera_position[1]) * s_y

        # cast ray until intersection
        intersection = False
        max_distance = 1000.0
        current_distance = 0.0
        intersection_x = None

        while ((not intersection) and (current_distance < max_distance)):

            # choose smaller ray length axis
            if ray_length_x < ray_length_y:

                # step in this axis to new grid sqaure
                grid_x += step_x

                # store current distance to new grid square
                current_distance = ray_length_x
                intersection_x = True

                # update ray length due to new step
                ray_length_x += s_x

            else:

                grid_y += step_y
                current_distance = ray_length_y
                intersection_x = False
                ray_length_y += s_y

            # check if intersection with new grid square
            if (grid_x >= 0) and (grid_x < self.n) and (grid_y >= 0) and (grid_y < self.n):
                if self.grid[grid_y][grid_x] == 1:
                    intersection = True
            else:
                break

        # threshold minimum distance: prevent zero division errors
        if current_distance < 0.1:
            current_distance = 0.1

        # return status and distance
        return intersection, current_distance, intersection_x


    def run(self):
        
        # loop
        while self.running:

            # clock
            self.dt = self.clock.tick(60)

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