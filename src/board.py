from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound
import copy
import os

class Board:

    def __init__(self):
        # 2D array
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0] for col in range(COLS)]
        self.last_move = None
        self.in_check_square = None
        self.check_mate = False
        # create the complete board
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    # moves in the console board
    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()

        # console board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):#
            #en passant capture
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                # console board move update
                self.squares[initial.row][initial.col + diff].piece = None
                self.squares[final.row][final.col].piece = piece
                # play capture sound
                if not testing:
                    sound = Sound(os.path.join(
                        'assets/sounds/capture.wav'
                    ))
                    sound.play()

            else:
                # pawn promotion
                self.check_promotion(piece, final)

        # king castling
        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook = piece.left_rook if (diff< 0) else piece.right_rook
                # sending the last move of the rook, which was recenly added in the king_moves method
                self.move(rook, rook.moves[-1])

        piece.moved = True

        # clear valid moves
        #piece.clear_moves()

        # set last move
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves
    
    # pawn promotion
    def check_promotion(self, piece, final):
        # pawn in rows 0 and 7 will alway be opposite color pawnss
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    # castling
    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2
    
    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn):
            return

        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    self.squares[row][col].piece.en_passant = False

        piece.en_passant = True

    # check if king is in check before making a move, to remove such move from the valid moves
    def in_check(self, piece, move):
        # self is the actual board; so copy the current state of the board
        temp_board = copy.deepcopy(self)
        # the piece making the move
        temp_piece = copy.deepcopy(piece)

        
        # make the move in the temp board
        temp_board.move(temp_piece, move, testing=True)

        # go through all  possible moves of all rival pieces
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_rival_piece(piece.color):
                    # get the rival piece
                    p = temp_board.squares[row][col].piece
                    # get all possible moves of the rival piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    # check if a possible move lands on a king
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        
        return False

    # get the king square if in check
    # piece = just moved piece
    def in_check_coords(self, piece):

        self.in_check_square = None
        self.check_mate = True
        
        # go through all  possible moves
        for row in range(ROWS):
            for col in range(COLS):
                # check if any of the team pieces create a check
                if self.squares[row][col].has_team_piece(piece.color):
                    # get the team piece
                    p = self.squares[row][col].piece
                    # get all possible moves of the team piece
                    self.calc_moves(p, row, col, bool=True)
                    # check if a possible final move lands on a king
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            self.in_check_square = m.final

                # if there arent any valid moves for any of the enemy pieces, it is a check mate
                elif self.squares[row][col].has_rival_piece(piece.color):
                    # get the rival piece
                    p = self.squares[row][col].piece
                    # get all possible moves of the rival piece
                    self.calc_moves(p, row, col, bool=True)
                    # if any move exists, no check mate
                    if p.moves:
                        self.check_mate = False

    # Calculate all the possible (valid) moves of a specific piece on a specific position
    def calc_moves(self, piece, row, col, bool=True):
        piece.clear_moves()
        def pawn_moves():
            # pawn steps
            steps = 1 if piece.moved else 2

            # vertical moves
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        # create initial and final move squares
                        initial = Square(row, col)
                        final = Square(possible_move_row, col)
                        # create new move
                        move = Move(initial, final)
                        # check potential checks
                        # bool is false if calc_moves() is called from the in_check() method, so there's no need to check again
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

                    # pawn is blocked if first square is not empty
                    else:
                        break
                # if first square is not in range, the following is also not in range
                else:
                    break

            # diagonal moves
            possible_move_row = row + piece.dir
            possible_move_cols = [col-1, col+1]
            for possible_move_col in possible_move_cols:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_rival_piece(piece.color):
                        # create move
                        initial = Square(row, col)
                        # save the piece that can be captured to check for possible checks
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                        else:
                            piece.add_move(move)
            
            # en passant moves
            r = 3 if piece.color == 'white' else 4
            final_row = 2 if piece.color == 'white' else 5

            # left en_passant
            if Square.in_range(col-1) and row == r:
                if self.squares[row][col-1].has_rival_piece(piece.color):
                    p = self.squares[row][col-1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            initial = Square(row, col)
                            final = Square(final_row, col-1, p)
                            move = Move(initial, final)

                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

            # right en_passant
            if Square.in_range(col+1) and row == r:
                if self.squares[row][col+1].has_rival_piece(piece.color):
                    p = self.squares[row][col+1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            initial = Square(row, col)
                            final = Square(final_row, col+1, p)
                            move = Move(initial, final)

                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)


        def knight_moves():
            # 8 possible moves
            possible_moves = [
                (row-2, col+1),
                (row-1, col+2),
                (row+1, col+2),
                (row+2, col+1),
                (row+2, col-1),
                (row+1, col-2),
                (row-1, col-2),
                (row-2, col-1),
            ]

            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move

                # if possible move is in range of the board
                if Square.in_range(possible_move_row, possible_move_col):
                    # if empty or contains a rival piece, it is valid move
                    if self.squares[possible_move_row][possible_move_col].isempty_or_rival(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        # create move
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                            else: break
                        else:
                            piece.add_move(move)

        def straightline_moves(incrs):
            for incr in incrs:
                row_incr, col_incr = incr
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while True:
                    if Square.in_range(possible_move_row, possible_move_col):

                        # create move because both if statements need a move
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)

                        # empty, continue looping
                        if self.squares[possible_move_row][possible_move_col].isempty():
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

                        # if there's a rival piece, add move and no need to keep checking more possible moves
                        elif self.squares[possible_move_row][possible_move_col].has_rival_piece(piece.color):
                            if bool:
                                if not self.in_check(piece, move):
                                    # append new move
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                            break

                        # if there's a team piece, break
                        elif self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
                            break

                    # not in range
                    else:
                        break

                    # incrementing the increments by incr
                    possible_move_row = possible_move_row + row_incr
                    possible_move_col = possible_move_col + col_incr
    
        def king_moves():
            adjs = [
                (row-1, col), # up
                (row-1, col+1), # up-right
                (row, col+1), # right
                (row+1, col+1), # down-right
                (row+1, col), # down
                (row+1, col-1), # down-left
                (row, col-1), # left
                (row-1, col-1), # up-left
            ]
            
            # normal moves
            for possible_move in adjs:
                possible_move_row, possible_move_col = possible_move

                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_rival(piece.color):
                        # create new move
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                # append new move
                                piece.add_move(move)
                            else: break
                        else:
                            piece.add_move(move)

            # castling moves
            if not piece.moved:
                # queen castling
                left_rook = self.squares[row][0].piece
                # check if the piece there is actually a rook
                if isinstance(left_rook, Rook):
                    # make sure the rook hasnt moved
                    if not left_rook.moved:
                        for c in range(1, 4):
                            # castling not possible because there are pieces in between
                            if self.squares[row][c].has_piece():
                                break
                            
                            if c == 3:
                                # add left rook to king
                                piece.left_rook = left_rook

                                # rook move
                                initial = Square(row, 0)
                                final = Square(row, 3)
                                moveR = Move(initial, final)
                                left_rook.add_move(moveR)

                                # king move
                                initial = Square(row, col)
                                final = Square(row, 2)
                                moveK = Move(initial, final)

                                if bool:
                                    if not self.in_check(piece, moveK) and not self.in_check(left_rook, moveR):
                                        # append new king move
                                        piece.add_move(moveK)
                                        # append new rook move
                                        left_rook.add_move(moveR)

                                else:
                                    # append new king move
                                    piece.add_move(moveK)
                                    # append new rook move
                                    left_rook.add_move(moveR)

                # king castling
                right_rook = self.squares[row][7].piece
                # check if the piece there is actually a rook
                if isinstance(right_rook, Rook):
                    # make sure the rook hasnt moved
                    if not right_rook.moved:
                        for c in range(5, 7):
                            # castling not possible because there are pieces in between
                            if self.squares[row][c].has_piece():
                                break
                            
                            if c == 6:
                                # add right rook to king
                                piece.right_rook = right_rook

                                # rook move
                                initial = Square(row, 7)
                                final = Square(row, 5)
                                moveR = Move(initial, final)

                                # king move
                                initial = Square(row, col)
                                final = Square(row, 6)
                                moveK = Move(initial, final)

                                if bool:
                                    if not self.in_check(piece, moveK) and not self.in_check(right_rook, moveR):
                                        # append new king move
                                        piece.add_move(moveK)
                                        # append new rook move
                                        right_rook.add_move(moveR)

                                else:
                                    # append new king move
                                    piece.add_move(moveK)
                                    # append new rook move
                                    right_rook.add_move(moveR)

        if isinstance(piece, Pawn): 
            pawn_moves()

        elif isinstance(piece, Knight): 
            knight_moves()

        elif isinstance(piece, Bishop): 
            straightline_moves([
                (-1, 1), # up-right
                (-1, -1), # up-left
                (1, 1), # down-right
                (1, -1), # down-left
            ])

        elif isinstance(piece, Rook): 
            straightline_moves([
                (-1, 0), # up
                (0, 1), # right
                (1, 0), # down
                (0, -1), # left
            ])

        elif isinstance(piece, Queen): 
            straightline_moves([
                (-1, 1), # up-right
                (-1, -1), # up-left
                (1, 1), # down-right
                (1, -1), # down-left
                (-1, 0), # up
                (0, 1), # right
                (1, 0), # down
                (0, -1), # left
            ])

        elif isinstance(piece, King): 
            king_moves()

    # private methods
    # creating our console board
    def _create(self):
        # loopig the 2D array and adding a square object instead of a 0
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)
    
    def _add_pieces(self, color):
        # row position of whites and blacks
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        # all pawns
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        # knights
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        # bishops
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        # rook
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        # queen
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))

        # king
        self.squares[row_other][4] = Square(row_other, 4, King(color))        

