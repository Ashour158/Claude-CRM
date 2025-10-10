// frontend/src/utils/validation.js
// Form validation utilities - Phase 7

import * as yup from 'yup';

// Email validation schema
export const emailSchema = yup.string()
  .email('Invalid email address')
  .required('Email is required');

// Password validation schema  
export const passwordSchema = yup.string()
  .min(8, 'Password must be at least 8 characters')
  .matches(/[a-z]/, 'Password must contain at least one lowercase letter')
  .matches(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .matches(/\d/, 'Password must contain at least one number')
  .matches(/[!@#$%^&*(),.?":{}|<>]/, 'Password must contain at least one special character')
  .required('Password is required');

// User validation schemas
export const loginSchema = yup.object().shape({
  email: emailSchema,
  password: yup.string().required('Password is required'),
});

export const accountSchema = yup.object().shape({
  name: yup.string()
    .required('Account name is required')
    .min(2, 'Account name must be at least 2 characters'),
  industry: yup.string().nullable(),
  email: yup.string().email('Invalid email').nullable(),
  phone: yup.string().nullable(),
});

export const contactSchema = yup.object().shape({
  firstName: yup.string().required('First name is required'),
  lastName: yup.string().required('Last name is required'),
  email: emailSchema,
  phone: yup.string().nullable(),
});

export const leadSchema = yup.object().shape({
  firstName: yup.string().required('First name is required'),
  lastName: yup.string().required('Last name is required'),
  email: emailSchema,
  status: yup.string().required('Status is required'),
});

export const dealSchema = yup.object().shape({
  name: yup.string().required('Deal name is required'),
  amount: yup.number().positive('Amount must be positive').required('Amount is required'),
  stage: yup.string().required('Stage is required'),
});

export const taskSchema = yup.object().shape({
  subject: yup.string().required('Subject is required'),
  dueDate: yup.date().required('Due date is required'),
  priority: yup.string().required('Priority is required'),
  status: yup.string().required('Status is required'),
});

export const validateForm = async (schema, values) => {
  try {
    await schema.validate(values, { abortEarly: false });
    return {};
  } catch (error) {
    const errors = {};
    error.inner.forEach((err) => {
      if (err.path) {
        errors[err.path] = err.message;
      }
    });
    return errors;
  }
};
