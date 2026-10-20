#!/usr/bin/env ruby

# abstract
#   malconv.rb:
#   converts original src ( from stdin or a file ) to malbolge code
#   and prints it to stdout
#
# ops
#   D ( j ): D=[D]
#   I ( i ): C=[D]
#   R ( * ): A=[D]=rotr1([D])
#   C ( p ): A=[D]=crazy(A,[D])
#   P ( < ): putc(A)
#   G ( / ): A=getc()
#   E ( v ): exit()
#   N ( o ): nop()
#   ?      : any ... map to N(o)
#
# src format
#   any spaces or lines begins with # ... ignored
#   single op ... e.g. G
#   multi ops ... e.g. N*5
#   fill ops  ... e.g. N>10 ( fill N just before address 10 )
#   example: N*5RDRDN>15E ... NNNNNRDRDNNNNNNE -> DCBA@""~~;:9876B

OPS = 'DIRCPGEN?'
OPBASES = [ 7, 65, 6, 29, 66, 84, 48, 35, 35 ]
opmap = OPS.each_char.with_index.with_object({}){|(c,i),h|
  h[c] = OPBASES[i]
}
pos = 0
$<.each{|src|
  next if src =~ /^\s*#/
  src.scan(/\s*([A-Z?])(([*>])(\d+))?/){|m|
    b = opmap[m[0]] or next warn "invalid op #{m[0]}"
    iter = 1
    if m[2]
      n = m[3].to_i
      if m[2] == ?*
        iter = n
      elsif m[2] == ?>
        next warn "invalid fill range >#{n}" if pos > n
        iter = n - pos
      else
        raise "not reached"
      end
    end
    iter.times{
      putc (b-pos)%94+33
      pos+=1
    }
  }
}
puts ''
