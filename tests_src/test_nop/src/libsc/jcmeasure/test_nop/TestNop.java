package libsc.jcmeasure.test_nop;

import javacard.framework.*;

public class TestNop extends Applet
{

    protected TestNop()
    {

    }

    public static void install(byte[] bArray, short bOffset, byte bLength)
    {
        new TestNop().register(bArray, (short)(bOffset + 1), bArray[bOffset]);
    }

    private void empty_process(APDU apdu)
    {
        byte[] buf = apdu.getBuffer();
        short round = Util.getShort(buf, ISO7816.OFFSET_P1);
        for (short i = 0; i < round; ++i)
        {

        }
    }

    private void test_process(APDU apdu)
    {
        byte[] buf = apdu.getBuffer();
        short round = Util.getShort(buf, ISO7816.OFFSET_P1);
        for (short i = 0; i < round; ++i)
        {

        }
    }

    public void process(APDU apdu)
    {
        if (selectingApplet())
        {
            return;
        }
        byte[] buffer = apdu.getBuffer();
        switch (buffer[ISO7816.OFFSET_INS])
        {
        case 0x01:
            empty_process(apdu);
            break;
        case 0x02:
            test_process(apdu);
            break;
        default:
            ISOException.throwIt(ISO7816.SW_INS_NOT_SUPPORTED);
            break;
        }
    }
}
