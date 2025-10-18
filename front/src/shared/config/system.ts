import { createSystem, defaultConfig } from '@chakra-ui/react'


const grey = {
  100: '#F5F4FC',
  200: '#D7D5E9',
  300: '#9896A9',
  400: '#9CA3AF',
  500: '#6B7280',
  600: '#374151',
}

const violet = {
  100: '#F3E8FF',
  200: '#E9D5FF',
  300: '#C4B5FD',
  400: '#A78BFA',
  500: '#8B5CF6',
  600: '#7C3AED',
}

const blue = {
  100: '#DBEAFE',
  200: '#BFDBFE',
  300: '#93C5FD',
  400: '#60A5FA',
  500: '#3B82F6',
  600: '#2563EB',
}

const rose = {
  100: '#FFE4E6',
  200: '#FECDD3',
  300: '#FDA4AF',
  400: '#FB7185',
  500: '#F43F5E',
  600: '#E11D48',
}


export const system = createSystem(defaultConfig, {
  theme: {
    tokens: {
      fonts: {
        heading: { value: 'Inter, ui-sans-serif, system-ui' },
        body: { value: 'Inter, ui-sans-serif, system-ui' },
      },
      colors: {
        grey: {
          100: { value: grey[100] },
          200: { value: grey[200] },
          300: { value: grey[300] },
          400: { value: grey[400] },
          500: { value: grey[500] },
          600: { value: grey[600] },
        },
        violet: {
          100: { value: violet[100] },
          200: { value: violet[200] },
          300: { value: violet[300] },
          400: { value: violet[400] },
          500: { value: violet[500] },
          600: { value: violet[600] },
        },
        blue: {
          100: { value: blue[100] },
          200: { value: blue[200] },
          300: { value: blue[300] },
          400: { value: blue[400] },
          500: { value: blue[500] },
          600: { value: blue[600] },
        },
        rose: {
          100: { value: rose[100] },
          200: { value: rose[200] },
          300: { value: rose[300] },
          400: { value: rose[400] },
          500: { value: rose[500] },
          600: { value: rose[600] },
        },

        // алиас под привычный "gray"
        gray: {
          100: { value: '{colors.grey.100}' },
          200: { value: '{colors.grey.200}' },
          300: { value: '{colors.grey.300}' },
          400: { value: '{colors.grey.400}' },
          500: { value: '{colors.grey.500}' },
          600: { value: '{colors.grey.600}' },
        },
      },
    },
  },
})
