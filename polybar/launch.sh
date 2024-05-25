polybar-msg cmd quit

if type "xrandr"; then
  for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    MONITOR=$m polybar main --config=/home/murad/.config/polybar/config.ini/ --reload &
  done
else
  polybar main --config=/home/murad/.config/polybar/config.ini/ --reload &
fi
