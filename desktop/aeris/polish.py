"""Pure sizing rules for the desktop workspace."""
COMPACT_WIDTH=1100

def compact_workspace(width):
    return width < COMPACT_WIDTH

def contrast_ratio(foreground, background):
    def luminance(color):
        channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
        linear=[c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4 for c in channels]
        return sum(c*w for c,w in zip(linear,(0.2126,0.7152,0.0722)))
    a,b=sorted((luminance(foreground),luminance(background)))
    return (b+0.05)/(a+0.05)
